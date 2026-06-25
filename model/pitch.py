import librosa
import numpy as np

AUDIO_FILE = "output_stems/vocals.wav"

HOP_LENGTH = 512
FMIN = librosa.note_to_hz("C2")
FMAX = librosa.note_to_hz("C7")


def extract_pitches(audio_path: str, hop_length: int = HOP_LENGTH):
    """
    Returns a list of dicts: [{time, frequency_hz, note, voiced, confidence}, ...]
    one entry per frame. frequency_hz is None for unvoiced/silent frames.
    """
    y, sr = librosa.load(audio_path, sr=None, mono=True)

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=FMIN,
        fmax=FMAX,
        sr=sr,
        hop_length=hop_length,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    results = []
    for t, freq, voiced, prob in zip(times, f0, voiced_flag, voiced_prob):
        is_voiced = bool(voiced) and freq is not None and not np.isnan(freq)
        note = librosa.hz_to_note(freq) if is_voiced else None
        results.append({
            "time": round(float(t), 4),
            "note": note,
        })

    return results


if __name__ == "__main__":
    pitches = extract_pitches(AUDIO_FILE)

    for entry in pitches:
        print(entry)

    print(f"\nExtracted {len(pitches)} frames from '{AUDIO_FILE}'")


# need to convert the data structure
