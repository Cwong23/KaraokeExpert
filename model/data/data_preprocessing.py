import librosa
import librosa.display
import numpy as np
import os

SOURCE_DIR = r"C:\Users\chris\Downloads\archive"
DEST_DIR = r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert\model\data\processed_data"

SPLITS = ["train", "test", "valid"]
SEGMENT_DURATION = 30
SR = 44100
N_FFT = 2048
HOP_LENGTH = 512

sample_counter = {split: 0 for split in SPLITS}


def make_dirs():
    for split in SPLITS:
        os.makedirs(os.path.join(DEST_DIR, split), exist_ok=True)


def get_magnitude(y):
    """Returns the absolute magnitude of the STFT."""
    stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    return np.abs(stft)


def normalize_spectrogram(magnitude, ref_max):
    """
    Normalizes magnitude to dB using a GLOBAL reference max,
    then scales to a [0, 1] range.
    """
    spec_db = librosa.amplitude_to_db(magnitude, ref=ref_max)
    spec_db = np.clip(spec_db, -80, 0)
    spec_db = (spec_db + 80) / 80
    return spec_db.astype(np.float32)


def process_song(split, song_dir):
    global sample_counter

    vocals_path = os.path.join(song_dir, "vocals.wav")
    mixture_path = os.path.join(song_dir, "mixture.wav")

    if not (os.path.exists(vocals_path) and os.path.exists(mixture_path)):
        return

    try:
        # Load audio (Forcing SR to 44100 for consistency)
        y_vocals, _ = librosa.load(vocals_path, sr=SR)
        y_mix, _ = librosa.load(mixture_path, sr=SR)

        # Ensure lengths match exactly
        min_len = min(len(y_vocals), len(y_mix))
        y_vocals = y_vocals[:min_len]
        y_mix = y_mix[:min_len]

        segment_samples = SEGMENT_DURATION * SR
        total_segments = int(min_len // segment_samples)

        for i in range(total_segments):
            start = int(i * segment_samples)
            end = int((i + 1) * segment_samples)

            # 1. Create Slices
            v_seg = y_vocals[start:end]
            m_seg = y_mix[start:end]
            i_seg = m_seg - v_seg

            # Skip silent segments (threshold of 1% max volume)
            if np.max(np.abs(v_seg)) < 0.01:
                continue

            # 2. Compute Raw Magnitudes
            mag_v = get_magnitude(v_seg)
            mag_m = get_magnitude(m_seg)
            mag_i = get_magnitude(i_seg)

            # 3. GET GLOBAL REFERENCE
            ref_max = np.max(mag_m)
            if ref_max < 1e-6:
                continue

            # 4. Normalize (all using the same ref_max)
            norm_v = normalize_spectrogram(mag_v[:1024, :], ref_max)
            norm_m = normalize_spectrogram(mag_m[:1024, :], ref_max)
            norm_i = normalize_spectrogram(mag_i[:1024, :], ref_max)

            # 5. Save Sample
            sample_id = sample_counter[split]
            sample_folder = os.path.join(
                DEST_DIR, split, f"sample_{sample_id:05d}")
            os.makedirs(sample_folder, exist_ok=True)

            np.save(os.path.join(sample_folder, "vocals.npy"), norm_v)
            np.save(os.path.join(sample_folder, "mixture.npy"), norm_m)
            np.save(os.path.join(sample_folder, "instrumental.npy"), norm_i)

            sample_counter[split] += 1

    except Exception as e:
        print(f"Error processing {song_dir}: {e}")


def main():
    print(f"Starting Preprocessing...")
    print(f"Source: {SOURCE_DIR}")
    print(f"Dest: {DEST_DIR}")

    make_dirs()

    for split in SPLITS:
        split_path = os.path.join(SOURCE_DIR, split)
        if not os.path.exists(split_path):
            print(f"Skipping {split} - folder not found.")
            continue

        songs = [s for s in os.listdir(split_path) if os.path.isdir(
            os.path.join(split_path, s))]
        print(f"Processing {len(songs)} songs in '{split}' split...")

        for song in songs:
            song_dir = os.path.join(split_path, song)
            process_song(split, song_dir)

    print("\nPreprocessing Complete!")
    for split in SPLITS:
        print(
            f"{split.capitalize()} samples generated: {sample_counter[split]}")


if __name__ == "__main__":
    main()
