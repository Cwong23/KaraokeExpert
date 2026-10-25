import argparse
import json
from pathlib import Path
import stempeg

import numpy as np

DEFAULT_INPUT = r"C:\Users\chris\Downloads\musdb18\test"
DEFAULT_OUTPUT = (
    r"C:\Users\chris\OneDrive\Desktop\senior-project\KaraokeExpert"
    r"\model\data\processed_data\pytorch_test"
)
SAMPLE_RATE = 44100
EPS = 1e-8

STEM_MIXTURE, STEM_DRUMS, STEM_BASS, STEM_OTHER, STEM_VOCALS = range(5)


def find_tracks(root: Path):
    """Return a sorted list of (name, kind, path) for every track found."""
    tracks = []
    for p in sorted(root.glob("*.stem.mp4")):
        tracks.append((p.name.replace(".stem.mp4", ""), "stem", p))
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if (d / "mixture.wav").exists() and (d / "vocals.wav").exists():
            tracks.append((d.name, "wav", d))
    return tracks


def load_stem_mp4(path: Path):
    """Return dict of (channels, samples) float32 arrays: mixture, vocals, instrumental."""

    stems, rate = stempeg.read_stems(
        str(path), dtype=np.float32)  # (5, samples, 2)
    if int(rate) != SAMPLE_RATE:
        raise ValueError(f"{path.name}: expected {SAMPLE_RATE} Hz, got {rate}")
    stems = np.transpose(stems, (0, 2, 1))  # -> (5, 2, samples)
    return {
        "mixture": stems[STEM_MIXTURE],
        "vocals": stems[STEM_VOCALS],
        "instrumental": stems[STEM_DRUMS] + stems[STEM_BASS] + stems[STEM_OTHER],
    }


def load_wav_folder(folder: Path):
    import soundfile as sf

    def read(name):
        x, rate = sf.read(
            str(folder / f"{name}.wav"), dtype="float32", always_2d=True)
        if rate != SAMPLE_RATE:
            raise ValueError(
                f"{folder.name}/{name}.wav: expected {SAMPLE_RATE} Hz, got {rate}")
        return x.T  # (channels, samples)

    return {
        "mixture": read("mixture"),
        "vocals": read("vocals"),
        "instrumental": read("drums") + read("bass") + read("other"),
    }


def center_clip(data, clip_seconds: float):
    """Take a centered clip of `clip_seconds` (no-op if 0 or the track is shorter)."""
    if clip_seconds <= 0:
        return data
    n = next(iter(data.values())).shape[-1]
    clip = int(clip_seconds * SAMPLE_RATE)
    if n <= clip:
        return data
    start = (n - clip) // 2
    return {k: v[:, start: start + clip] for k, v in data.items()}


def sum_check_db(data) -> float:
    """How closely vocals + instrumental reproduce the mixture (dB, higher = better)."""
    mix = data["mixture"]
    err = mix - (data["vocals"] + data["instrumental"])
    return float(10 * np.log10((np.sum(mix**2) + EPS) / (np.sum(err**2) + EPS)))


def main():
    p = argparse.ArgumentParser(
        description="Prepare MUSDB18 test split for SDR evaluation")
    p.add_argument("--input", default=DEFAULT_INPUT)
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--clip-seconds", type=float, default=30.0,
                   help="Centered clip length per track; 0 keeps full tracks (default: 30)")
    p.add_argument("--limit", type=int, default=0,
                   help="Only process the first N tracks")
    p.add_argument("--overwrite", action="store_true",
                   help="Re-create samples that already exist")
    args = p.parse_args()

    in_root, out_root = Path(args.input), Path(args.output)
    if not in_root.exists():
        raise SystemExit(f"Input folder not found: {in_root}")

    tracks = find_tracks(in_root)
    if not tracks:
        raise SystemExit(
            f"No tracks found in {in_root}. Expected *.stem.mp4 files or "
            "per-track folders containing mixture.wav / vocals.wav / ..."
        )
    if args.limit > 0:
        tracks = tracks[: args.limit]

    out_root.mkdir(parents=True, exist_ok=True)
    metadata = {}
    print(f"Found {len(tracks)} track(s). Writing to {out_root}\n")

    for i, (name, kind, path) in enumerate(tracks):
        sample_name = f"sample_{i:05d}"
        sample_dir = out_root / sample_name
        metadata[sample_name] = name

        done = all((sample_dir / f"{s}.npy").exists()
                   for s in ("mixture", "vocals", "instrumental"))
        if done and not args.overwrite:
            print(f"[{i + 1}/{len(tracks)}] {sample_name} exists, skipping ({name})")
            continue

        data = load_stem_mp4(path) if kind == "stem" else load_wav_folder(path)
        data = center_clip(data, args.clip_seconds)
        check = sum_check_db(data)

        sample_dir.mkdir(parents=True, exist_ok=True)
        for key, arr in data.items():
            np.save(sample_dir / f"{key}.npy",
                    np.ascontiguousarray(arr, dtype=np.float32))

        secs = data["mixture"].shape[-1] / SAMPLE_RATE
        flag = "" if check > 20 else "  <-- stems don't sum to mixture, check this track"
        print(f"[{i + 1}/{len(tracks)}] {sample_name} <- {name} "
              f"({secs:.1f}s, v+i vs mix {check:.1f} dB){flag}")

    with open(out_root / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nDone. Point evaluate() at: {out_root}")


if __name__ == "__main__":
    main()
