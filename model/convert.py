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


def reconstruct(data, sr):
    db = (np.clip(data, 0, 1) * 80.0) - 80.0
    amp = librosa.db_to_amplitude(db)

    return librosa.griffinlim(
        amp, n_iter=128, hop_length=HOP_LENGTH, win_length=N_FFT, momentum=0.99
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

print("Reconstructing audio...")
wav_vocals = reconstruct(final_pred_npy, SR)

output_path = os.path.join(DEST_DIR, "extracted_vocals.wav")
sf.write(output_path, wav_vocals, SR)

print(f"Success! Vocals saved to: {output_path}")
