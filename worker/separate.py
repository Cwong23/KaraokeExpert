import io
import logging
from dataclasses import dataclass, field

import torch
import torchaudio
from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB_PLUS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class Config:
    device: torch.device = field(
        default_factory=lambda: torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
    )


def separate_audio(
    input_buffer: io.BytesIO, cfg: Config
) -> tuple[io.BytesIO, io.BytesIO]:
    """
    Separate an in-memory audio buffer into vocal / instrumental streams.

    Returns (vocal_stream, instrumental_stream) as BytesIO objects
    containing WAV data, positioned at offset 0 and ready to read/upload.
    """
    log.info("Using device: %s", cfg.device)

    log.info("Loading pre-trained Hybrid Demucs model...")
    bundle = HDEMUCS_HIGH_MUSDB_PLUS
    model = bundle.get_model().to(cfg.device)
    model.eval()

    # Demucs native source order
    stem_names = ["drums", "bass", "other", "vocals"]

    input_buffer.seek(0)
    waveform, sample_rate = torchaudio.load(input_buffer)

    # Resample to the model's native rate if needed
    if sample_rate != bundle.sample_rate:
        log.info("Resampling from %dHz to %dHz...",
                 sample_rate, bundle.sample_rate)
        resampler = torchaudio.transforms.Resample(
            sample_rate, bundle.sample_rate)
        waveform = resampler(waveform)
        sample_rate = bundle.sample_rate

    # Normalize volume profile to prepare for model tracking
    ref_mean = waveform.mean()
    ref_std = waveform.std()
    waveform = (waveform - ref_mean) / ref_std

    # Add batch dimension [channels, frames] -> [1, channels, frames]
    waveform = waveform.to(cfg.device).unsqueeze(0)

    log.info("Processing audio track with Demucs native windowing...")
    with torch.no_grad():
        separated_tensor = model(waveform)
        # Remove batch dim -> [stems, channels, frames]
        separated_tensor = separated_tensor.squeeze(0)

    # Re-apply original variance to recover mix balance
    separated_tensor = (separated_tensor * ref_std) + ref_mean

    drums = separated_tensor[stem_names.index("drums")]
    bass = separated_tensor[stem_names.index("bass")]
    other = separated_tensor[stem_names.index("other")]
    vocals = separated_tensor[stem_names.index("vocals")]
    instrumental = drums + bass + other

    instr_stream = io.BytesIO()
    vocal_stream = io.BytesIO()

    torchaudio.save(
        instr_stream, instrumental.cpu(), sample_rate, format="wav")
    torchaudio.save(
        vocal_stream, vocals.cpu(), sample_rate, format="wav")

    instr_stream.seek(0)
    vocal_stream.seek(0)

    log.info("Separation pipeline completed successfully!")
    return vocal_stream, instr_stream
