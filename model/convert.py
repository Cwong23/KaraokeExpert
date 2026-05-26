# py -3.11 ./convert.py

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch

from unet import UNetModel

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class Config:
    source_file: str = r"C:\Users\chris\Downloads\locked.mp3"
    dest_dir: str = r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert\model\data\testing_output"
    model_path: str = "resulting_model/unet_epoch_50.pth"

    # Audio
    sr: int = 44_100
    n_fft: int = 2_048
    hop_length: int = 512
    freq_bins: int = 1_024

    # Chunking
    chunk_w: int = 512   # spectrogram frames per model call
    overlap: float = 0.5  # fraction of chunk to overlap between adjacent calls

    # Masking  — Wiener-style soft mask: v^P / (v^P + i^P)
    wiener_exp: float = 2.0
    vocal_suppress: float = 0.85

    inst_force_low: int = 20
    inst_force_high: int = 800

    device: torch.device = field(
        default_factory=lambda: torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
    )


def audio_to_spec(
    y: np.ndarray, cfg: Config
) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Convert a mono waveform to a normalised log-magnitude spectrogram.

    spec_norm   : float32 array [freq_bins, T] in [0, 1]
    stft        : complex STFT (full n_fft//2+1 bins)
    ref_max     : amplitude reference used for normalisation
    """
    stft = librosa.stft(y, n_fft=cfg.n_fft, hop_length=cfg.hop_length)
    magnitude = np.abs(stft)
    ref_max = magnitude.max() or 1.0          # guard against silence
    spec_db = librosa.amplitude_to_db(magnitude, ref=ref_max)
    # Map [−80, 0] dB → [0, 1]; clip outside that range
    spec_norm = np.clip((spec_db + 80.0) / 80.0, 0.0, 1.0).astype(np.float32)
    # Drop the Nyquist bin so height == cfg.freq_bins (model expectation)
    return spec_norm[: cfg.freq_bins], stft, ref_max


def apply_mask_and_reconstruct(
    mask: np.ndarray,
    mix_spec: np.ndarray,
    stft: np.ndarray,
    ref_max: float,
    cfg: Config,
) -> np.ndarray:
    """
    Apply a [0,1] magnitude mask to the normalised spectrogram, then
    reconstruct a waveform via iSTFT, reusing the original phase.
    """
    masked_norm = mix_spec * mask
    db = (masked_norm * 80.0) - 80.0
    amp = librosa.db_to_amplitude(db, ref=ref_max)

    T = amp.shape[1]
    # Pad back to full STFT height
    n_stft_bins = cfg.n_fft // 2 + 1
    if amp.shape[0] < n_stft_bins:
        pad_rows = n_stft_bins - amp.shape[0]
        amp = np.vstack([amp, np.zeros((pad_rows, T), dtype=np.float32)])

    phase = np.exp(1j * np.angle(stft[:, :T]))
    return librosa.istft(amp * phase, hop_length=cfg.hop_length)


def run_model_ola(
    mix_spec: np.ndarray,
    model: torch.nn.Module,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Run the model over the full spectrogram using overlap-add to eliminate
    chunk boundary artefacts.

    Returns vocal_mask and inst_mask, both float32 [freq_bins, T].
    """
    freq_bins, n_frames = mix_spec.shape
    step = max(1, int(cfg.chunk_w * (1.0 - cfg.overlap)))
    win = np.hanning(cfg.chunk_w).astype(np.float32)

    # Pad so the last chunk is fully covered
    pad = (cfg.chunk_w - n_frames % cfg.chunk_w) % cfg.chunk_w
    padded = np.pad(mix_spec, ((0, 0), (0, pad)), mode="constant")
    n_padded = padded.shape[1]

    v_acc = np.zeros((freq_bins, n_padded), dtype=np.float32)
    i_acc = np.zeros((freq_bins, n_padded), dtype=np.float32)
    w_acc = np.zeros(n_padded, dtype=np.float32)

    starts = range(0, n_padded - cfg.chunk_w + 1, step)
    log.info("Running model over %d chunks (OLA step=%d)…", len(starts), step)

    with torch.no_grad():
        for start in starts:
            chunk = padded[:, start: start + cfg.chunk_w]
            x = torch.from_numpy(chunk).unsqueeze(
                0).unsqueeze(0).to(cfg.device)
            logits = model(x).squeeze(0)
            probs = torch.sigmoid(logits).cpu().numpy()

            v_acc[:, start: start + cfg.chunk_w] += probs[0] * win
            i_acc[:, start: start + cfg.chunk_w] += probs[1] * win
            w_acc[start: start + cfg.chunk_w] += win

    # Normalise by accumulated window weights (safe division)
    w_acc = np.maximum(w_acc, 1e-8)
    v_mask_raw = v_acc / w_acc
    i_mask_raw = i_acc / w_acc

    return v_mask_raw[:, :n_frames], i_mask_raw[:, :n_frames]


def build_masks(
    v_raw: np.ndarray,
    i_raw: np.ndarray,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Derive final vocal / instrumental masks from raw model outputs.

    Uses a Wiener-style soft mask so the two stems are complementary and
    sum back to the original mixture (before the hard-force overrides).
    """
    eps = 1e-10
    P = cfg.wiener_exp
    v_p, i_p = v_raw**P, i_raw**P

    # Soft Wiener mask: v^P / (v^P + i^P)  ∈ [0, 1]
    v_mask = v_p / (v_p + i_p + eps)

    # Instrumental mask: attenuate vocal regions by vocal_suppress
    inst_mask = 1.0 - v_mask * cfg.vocal_suppress

    # Hard-force known non-vocal frequency bands to pass through fully
    inst_mask[: cfg.inst_force_low, :] = 1.0
    inst_mask[cfg.inst_force_high:, :] = 1.0

    return v_mask, inst_mask


def separate_channel(
    y: np.ndarray,
    model: torch.nn.Module,
    cfg: Config,
) -> tuple[np.ndarray, np.ndarray]:
    """Separate a single mono channel; return (vocal_wav, inst_wav)."""
    mix_spec, stft, ref_max = audio_to_spec(y, cfg)
    v_raw, i_raw = run_model_ola(mix_spec, model, cfg)
    v_mask, inst_mask = build_masks(v_raw, i_raw, cfg)

    wav_v = apply_mask_and_reconstruct(v_mask, mix_spec, stft, ref_max, cfg)
    wav_i = apply_mask_and_reconstruct(inst_mask, mix_spec, stft, ref_max, cfg)
    return wav_v, wav_i


def peak_match(stem: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Scale *stem* so its peak matches the peak amplitude of *reference*."""
    ref_peak = np.max(np.abs(reference))
    stem_peak = np.max(np.abs(stem))
    if stem_peak < 1e-8:
        return stem
    return stem * (ref_peak / stem_peak)


def stack(channels):
    max_len = max(c.shape[0] for c in channels)
    padded = [np.pad(c, (0, max_len - c.shape[0])) for c in channels]
    arr = np.stack(padded, axis=0)          # (C, N)
    return arr.squeeze(0) if arr.shape[0] == 1 else arr.T


def main() -> None:
    cfg = Config()
    dest = Path(cfg.dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    log.info("Loading model from %s on %s", cfg.model_path, cfg.device)
    model = UNetModel(in_channels=1, out_channels=2).to(cfg.device)
    model.load_state_dict(torch.load(cfg.model_path, map_location=cfg.device))
    model.eval()

    log.info("Loading audio: %s", cfg.source_file)
    y_raw, _ = librosa.load(cfg.source_file, sr=cfg.sr, mono=False)

    if y_raw.ndim == 1:
        y_raw = y_raw[np.newaxis, :]    # mono → (1, N)
    n_channels = y_raw.shape[0]
    log.info("Audio: %d channel(s), %.1f s",
             n_channels, y_raw.shape[1] / cfg.sr)

    v_channels, i_channels = [], []
    for ch in range(n_channels):
        log.info("Separating channel %d/%d…", ch + 1, n_channels)
        wav_v, wav_i = separate_channel(y_raw[ch], model, cfg)
        v_channels.append(wav_v)
        i_channels.append(wav_i)

    wav_v = stack(v_channels)
    wav_i = stack(i_channels)

    y_mix_mono = y_raw.mean(axis=0)
    wav_v = peak_match(wav_v, y_mix_mono)
    wav_i = peak_match(wav_i, y_mix_mono)

    out_v = dest / "vocals.wav"
    out_i = dest / "instrumental.wav"
    sf.write(out_v, wav_v, cfg.sr)
    sf.write(out_i, wav_i, cfg.sr)
    log.info("Saved: %s", out_v)
    log.info("Saved: %s", out_i)


if __name__ == "__main__":
    main()
