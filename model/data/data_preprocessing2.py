import librosa
import numpy as np
import os

SOURCE_DIR = r"C:\Users\chris\Downloads\DSD100\DSD100"
DEST_DIR = r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert\model\data\processed_data"

SPLITS = {
    "Dev":  "train",
    "Test": "test",
}

SEGMENT_DURATION = 30
SR = 44100
N_FFT = 2048
HOP_LENGTH = 512


def get_starting_counter(dest_dir):
    counter = {}
    for split in ["train", "test", "valid"]:
        split_path = os.path.join(dest_dir, split)
        if os.path.exists(split_path):
            existing = [d for d in os.listdir(
                split_path) if d.startswith("sample_")]
            counter[split] = len(existing)
        else:
            counter[split] = 0
    print("Starting counters:")
    for split, count in counter.items():
        print(f"  {split}: {count} existing samples")
    return counter


def make_dirs():
    for split in ["train", "test", "valid"]:
        os.makedirs(os.path.join(DEST_DIR, split), exist_ok=True)


def get_norm_spec(y, ref_max):
    """Computes STFT and normalizes using a global reference max."""
    stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    magnitude = np.abs(stft)
    # Crop to 1024 bins for U-Net compatibility
    magnitude = magnitude[:1024, :]

    spec_db = librosa.amplitude_to_db(magnitude, ref=ref_max)
    spec_db = np.clip(spec_db, -80, 0)
    spec_db = (spec_db + 80) / 80
    return spec_db.astype(np.float32)


def load_and_resample(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    return y


def process_song(dest_split, mixture_path, sources_dir, sample_counter):
    stems = ["vocals", "bass", "drums", "other"]
    paths = {s: os.path.join(sources_dir, f"{s}.wav") for s in stems}
    paths['mixture'] = mixture_path

    for p in paths.values():
        if not os.path.exists(p):
            print(f"  Missing: {p}, skipping.")
            return

    try:
        y_mix = load_and_resample(paths['mixture'])
        y_vocals = load_and_resample(paths['vocals'])
        y_bass = load_and_resample(paths['bass'])
        y_drums = load_and_resample(paths['drums'])
        y_other = load_and_resample(paths['other'])

        min_len = min(len(y_mix), len(y_vocals), len(
            y_bass), len(y_drums), len(y_other))

        # Clean segmenting
        segment_samples = SEGMENT_DURATION * SR
        total_segments = min_len // segment_samples

        for i in range(total_segments):
            start = i * segment_samples
            end = start + segment_samples

            mix_seg = y_mix[start:end]
            vocals_seg = y_vocals[start:end]
            # Construct instrumental from stems
            instr_seg = y_bass[start:end] + \
                y_drums[start:end] + y_other[start:end]

            if np.max(np.abs(vocals_seg)) < 0.01:
                continue

            # 1. Get raw magnitude of mixture to find global peak
            mix_stft = librosa.stft(
                mix_seg, n_fft=N_FFT, hop_length=HOP_LENGTH)
            mix_mag = np.abs(mix_stft)
            ref_max = np.max(mix_mag)

            if ref_max < 1e-6:
                continue

            # 2. Normalize all using ref_max
            norm_mix = get_norm_spec(mix_seg, ref_max)
            norm_vocals = get_norm_spec(vocals_seg, ref_max)
            norm_instr = get_norm_spec(instr_seg, ref_max)

            sample_id = sample_counter[dest_split]
            sample_folder = os.path.join(
                DEST_DIR, dest_split, f"sample_{sample_id:05d}")
            os.makedirs(sample_folder, exist_ok=True)

            np.save(os.path.join(sample_folder, "mixture.npy"), norm_mix)
            np.save(os.path.join(sample_folder, "vocals.npy"), norm_vocals)
            np.save(os.path.join(sample_folder, "instrumental.npy"), norm_instr)

            sample_counter[dest_split] += 1
            if sample_id % 10 == 0:
                print(f"  Processed {dest_split} up to sample_{sample_id:05d}")

    except Exception as e:
        print(f"  Error: {e}")


def main():
    make_dirs()
    sample_counter = get_starting_counter(DEST_DIR)

    for dsd_split, dest_split in SPLITS.items():
        mixtures_dir = os.path.join(SOURCE_DIR, "Mixtures", dsd_split)
        sources_dir = os.path.join(SOURCE_DIR, "Sources",  dsd_split)

        if not os.path.exists(mixtures_dir):
            print(f"Skipping {dsd_split} — not found")
            continue

        songs = sorted(os.listdir(mixtures_dir))
        print(f"\nProcessing {dsd_split} ({len(songs)} songs) → {dest_split}")

        for song in songs:
            mixture_path = os.path.join(mixtures_dir, song, "mixture.wav")
            song_sources = os.path.join(sources_dir, song)
            process_song(dest_split, mixture_path,
                         song_sources, sample_counter)

    print("\nDone.")
    for split, count in sample_counter.items():
        print(f"  {split}: {count} total samples")


if __name__ == "__main__":
    main()
