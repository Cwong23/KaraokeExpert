import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os

SOURCE_DIR = r"..."
DEST_DIR = r"..."

SPLITS = ["train", "test", "valid"]
SEGMENT_DURATION = 30

sample_counter = {split: 0 for split in SPLITS}


def make_dirs():
    for split in SPLITS:
        os.makedirs(os.path.join(DEST_DIR, split), exist_ok=True)


def save_spectrogram(y, sr, save_path):
    spectrogram = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_mels=128,
        n_fft=2048,
        hop_length=512
    )
    spectrogram_dB = librosa.power_to_db(spectrogram, ref=np.max)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(spectrogram_dB, sr=sr)
    plt.axis('off')
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()


def process_song(split, song_dir):
    global sample_counter

    vocals_path = os.path.join(song_dir, "vocals.wav")
    mixture_path = os.path.join(song_dir, "mixture.wav")

    if not (os.path.exists(vocals_path) and os.path.exists(mixture_path)):
        return

    try:
        y_vocals, sr = librosa.load(vocals_path, sr=None)
        y_mix, _ = librosa.load(mixture_path, sr=None)

        segment_length = SEGMENT_DURATION * sr
        total_segments = int(min(len(y_vocals), len(y_mix)) // segment_length)

        for i in range(total_segments):
            start = int(i * segment_length)
            end = int((i + 1) * segment_length)

            vocals_seg = y_vocals[start:end]
            mix_seg = y_mix[start:end]

            if len(vocals_seg) < sr or len(mix_seg) < sr:
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
            save_spectrogram(vocals_seg, sr,
                             os.path.join(sample_folder, "vocals.png"))

            save_spectrogram(mix_seg, sr,
                             os.path.join(sample_folder, "mixture.png"))

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
