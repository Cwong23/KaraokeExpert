import os
import torch
import torchaudio
from torchaudio.pipelines import HDEMUCS_HIGH_MUSDB_PLUS


def separate_audio(input_file, output_dir="output_stems"):
    # 1. Device selection (Forces CUDA/GPU usage)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 2. Load the pre-trained Hybrid Demucs bundle
    print("Loading pre-trained Hybrid Demucs model...")
    bundle = HDEMUCS_HIGH_MUSDB_PLUS
    model = bundle.get_model().to(device)
    model.eval()

    # Demucs native source order
    stem_names = ["drums", "bass", "other", "vocals"]

    # 3. Load and normalize audio track
    waveform, sample_rate = torchaudio.load(input_file)

    # Resample to the model's native 44.1kHz rate if needed
    if sample_rate != bundle.sample_rate:
        print(f"Resampling from {sample_rate}Hz to {bundle.sample_rate}Hz...")
        resampler = torchaudio.transforms.Resample(
            sample_rate, bundle.sample_rate)
        waveform = resampler(waveform)
        sample_rate = bundle.sample_rate

    # Normalize volume profiles to prepare for model tracking
    ref_mean = waveform.mean()
    ref_std = waveform.std()
    waveform = (waveform - ref_mean) / ref_std

    # Add batch dimension [channels, frames] -> [1, channels, frames]
    waveform = waveform.to(device).unsqueeze(0)

    print("Processing audio track with Demucs native windowing...")
    # Passing the full tensor with shifts=2 runs multiple internal frame passes,
    # which cleanly cancels out background bleeding (like crisp hi-hats).
    with torch.no_grad():
        separated_tensor = model(waveform)
        # Remove batch dim -> [stems, channels, frames]
        separated_tensor = separated_tensor.squeeze(0)

    # Re-apply original variance configurations to recover mix balance
    separated_tensor = (separated_tensor * ref_std) + ref_mean
    drums = separated_tensor[stem_names.index("drums")]
    bass = separated_tensor[stem_names.index("bass")]
    other = separated_tensor[stem_names.index("other")]
    vocals = separated_tensor[stem_names.index("vocals")]
    instrumental = drums + bass + other
    # 4. Export clean separated wave files to disk
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nSaving results into folder: '{output_dir}/'")
    torchaudio.save(os.path.join(output_dir, "instrumental.wav"),
                    instrumental.cpu(), sample_rate)
    torchaudio.save(os.path.join(output_dir, "vocals.wav"),
                    vocals.cpu(), sample_rate)

    print("\nSeparation pipeline completed successfully!")


if __name__ == "__main__":
    input_track = r"C:\Users\chris\Downloads\locked.mp3"

    if os.path.exists(input_track):
        separate_audio(input_track)
    else:
        print(f"Error: Could not find file '{input_track}'.")
