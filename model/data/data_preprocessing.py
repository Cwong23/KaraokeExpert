import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os

SOURCE_DIR = r"C:\Users\chris\Downloads\archive"
DEST_DIR = r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert\model\data\processed_data"

SPLITS = ["train", "test", "valid"]
SEGMENT_DURATION = 30

sample_counter = {split: 0 for split in SPLITS}


def make_dirs():
    for split in SPLITS:
        os.makedirs(os.path.join(DEST_DIR, split), exist_ok=True)


def save_stft_spectrogram(y, sr, save_path):
    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    magnitude = np.abs(stft)
    spec_db = librosa.amplitude_to_db(magnitude, ref=np.max)
    spec_db = np.clip(spec_db, -80, 0)
    spec_db = (spec_db + 80) / 80

    np.save(save_path, spec_db.astype(np.float32))


def process_song(split, song_dir):
    global sample_counter

    vocals_path = os.path.join(song_dir, "vocals.wav")
    mixture_path = os.path.join(song_dir, "mixture.wav")

    if not (os.path.exists(vocals_path) and os.path.exists(mixture_path)):
        return

    try:
        y_vocals, sr = librosa.load(vocals_path, sr=None)
        y_mix, sr_mix = librosa.load(mixture_path, sr=None)

        if sr_mix != sr:
            y_mix = librosa.resample(y_mix, orig_sr=sr_mix, target_sr=sr)

        segment_length = SEGMENT_DURATION * sr
        total_segments = int(min(len(y_vocals), len(y_mix)) // segment_length)

        for i in range(total_segments):
            start = int(i * segment_length)
            end = int((i + 1) * segment_length)

            vocals_seg = y_vocals[start:end]
            mix_seg = y_mix[start:end]

            if np.max(np.abs(vocals_seg)) < 0.01:
                continue

            # Create sample folder
            sample_id = sample_counter[split]
            sample_counter[split] += 1

            sample_folder = os.path.join(
                DEST_DIR,
                split,
                f"sample_{sample_id:05d}"
            )
            os.makedirs(sample_folder, exist_ok=True)

            # Save spectrograms
            save_stft_spectrogram(vocals_seg, sr,
                                  os.path.join(sample_folder, "vocals.npy"))

            save_stft_spectrogram(mix_seg, sr,
                                  os.path.join(sample_folder, "mixture.npy"))

    except Exception as e:
        print(f"Error processing {song_dir}: {e}")


def main():
    make_dirs()

    for split in SPLITS:
        split_path = os.path.join(SOURCE_DIR, split)

        if not os.path.exists(split_path):
            print(f"Skipping {split}")
            continue

        for song in os.listdir(split_path):
            song_dir = os.path.join(split_path, song)

            if os.path.isdir(song_dir):
                print(f"Processing {split}/{song}")
                process_song(split, song_dir)


if __name__ == "__main__":
    main()
