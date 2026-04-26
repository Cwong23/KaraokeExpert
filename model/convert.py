import torch
import numpy as np
import librosa
import soundfile as sf
import os
from unet import UNetModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SR = 44100
TARGET_W = 1024
N_FFT = 2048
HOP_LENGTH = 512

# Paths
SOURCE_FILE = r"C:\Users\chris\Downloads\still.mp3"
DEST_DIR = r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert\model\data\testing_output"
os.makedirs(DEST_DIR, exist_ok=True)

# Load Model
model = UNetModel(in_channels=1, out_channels=1).to(DEVICE)
model.load_state_dict(torch.load(
    "resulting_model/unet_final.pth", map_location=DEVICE))
model.eval()


def audio_to_spec(y):
    # Compute STFT
    stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    magnitude = np.abs(stft)

    # Convert to normalized dB [0, 1]
    spec_db = librosa.amplitude_to_db(magnitude, ref=np.max)
    spec_db = np.clip(spec_db, -80, 0)
    spec_db = (spec_db + 80) / 80
    # Return phase for better quality later if needed
    return spec_db, np.angle(stft)


def spec_to_amp(spec_data):
    db = (np.clip(spec_data, 0, 1) * 80.0) - 80.0
    return librosa.db_to_amplitude(db)


def reconstruct(data, sr):
    db = (np.clip(data, 0, 1) * 80.0) - 80.0
    amp = librosa.db_to_amplitude(db)

    if amp.shape[0] == 1024:
        padding = np.zeros((1, amp.shape[1]))
        amp = np.vstack([amp, padding])

    return librosa.griffinlim(
        amp,
        n_iter=128,
        hop_length=512,
        win_length=2048,
        momentum=0.99
    )


print(f"Loading {os.path.basename(SOURCE_FILE)}...")
y_mix, sr_mix = librosa.load(SOURCE_FILE, sr=SR)

mix_spec, _ = audio_to_spec(y_mix)
original_h, original_w = mix_spec.shape

print(f"Spectrogram shape: {mix_spec.shape}. Processing in chunks...")

mix_input = mix_spec[:1024, :]
pad_amount = TARGET_W - (original_w % TARGET_W)
mix_padded = np.pad(mix_input, ((0, 0), (0, pad_amount)), mode='constant')

processed_chunks = []

with torch.no_grad():
    for i in range(0, mix_padded.shape[1], TARGET_W):
        chunk = mix_padded[:, i:i+TARGET_W]

        tensor_chunk = torch.from_numpy(
            chunk).float().unsqueeze(0).unsqueeze(0).to(DEVICE)

        output_chunk = model(tensor_chunk)
        processed_chunks.append(output_chunk.squeeze().cpu().numpy())

full_pred = np.concatenate(processed_chunks, axis=1)
pred_npy = full_pred[:, :original_w]
final_pred_npy = np.vstack(
    [pred_npy, np.zeros((1, original_w))])

print("Reconstructing vocal audio...")
wav_vocals = reconstruct(final_pred_npy, SR)

print("Applying Spectral Masking...")
vocal_map = np.clip(full_pred, 0, 1)
mix_map = np.clip(mix_padded, 0, 1)

eps = 1e-10
vocal_mask = vocal_map / (mix_map + eps)
vocal_mask = np.clip(vocal_mask, 0, 1)
inst_mask = 1.0 - vocal_mask

final_inst_spec = mix_map * inst_mask

final_inst_spec = final_inst_spec[:, :original_w]


print(f"Reconstructing instrumental with shape: {final_inst_spec.shape}")
wav_instrumental = reconstruct(final_inst_spec, SR)

output_path_vocals = os.path.join(DEST_DIR, "extracted_vocals.wav")
sf.write(output_path_vocals, wav_vocals, SR)
print(f"Success! Vocals saved to: {output_path_vocals}")

output_path_instrumental = os.path.join(DEST_DIR, "extracted_instrumental.wav")
sf.write(output_path_instrumental, wav_instrumental, SR)
print(f"Success! Instrumentals saved to: {output_path_instrumental}")
