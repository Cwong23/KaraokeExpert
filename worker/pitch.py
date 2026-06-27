# import io
# import librosa
# import numpy as np

# HOP_LENGTH = 512
# FMIN = librosa.note_to_hz("C2")
# FMAX = librosa.note_to_hz("C7")

# NOTE_ORDER = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


# def note_distance(a: str, b: str) -> int:
#     def parse(n):
#         octave = int(n[-1])
#         name = n[:-1].replace('♯', '#')
#         return octave * 12 + NOTE_ORDER.index(name)
#     return abs(parse(a) - parse(b))


# def extract_pitches(
#     audio_buffer: io.BytesIO,
#     hop_length: int = HOP_LENGTH,
#     max_gap: float = 0.1,
#     max_semitones: int = 1,
# ) -> list[dict]:
#     """
#     Extracts vocal pitches from an audio buffer and returns them grouped
#     into sustained notes.

#     Returns a list of:
#         { "note": str, "start": float, "end": float, "duration": float }
#     """
#     audio_buffer.seek(0)
#     y, sr = librosa.load(audio_buffer, sr=None, mono=True)

#     f0, voiced_flag, voiced_prob = librosa.pyin(
#         y, fmin=FMIN, fmax=FMAX, sr=sr, hop_length=hop_length)

#     times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

#     groups = []
#     current_note = None
#     current_start = None
#     last_note_time = None
#     note_counts: dict[str, int] = {}

#     for t, freq, voiced, _ in zip(times, f0, voiced_flag, voiced_prob):
#         is_voiced = bool(voiced) and freq is not None and not np.isnan(freq)
#         note = librosa.hz_to_note(freq) if is_voiced else None
#         time = round(float(t), 4)

#         if note is None:
#             if current_note is not None and (time - last_note_time) > max_gap:
#                 groups.append({
#                     "note": max(note_counts, key=note_counts.get),
#                     "start": current_start,
#                     "end": last_note_time,
#                     "duration": round(last_note_time - current_start, 4),
#                 })
#                 current_note = None
#                 current_start = None
#                 last_note_time = None
#                 note_counts = {}
#             continue

#         if current_note is None or note_distance(note, current_note) > max_semitones:
#             if current_note is not None:
#                 groups.append({
#                     "note": max(note_counts, key=note_counts.get),
#                     "start": current_start,
#                     "end": last_note_time,
#                     "duration": round(last_note_time - current_start, 4),
#                 })
#                 note_counts = {}
#             current_note = note
#             current_start = time

#         note_counts[note] = note_counts.get(note, 0) + 1
#         last_note_time = time

#     if current_note is not None:
#         groups.append({
#             "note": max(note_counts, key=note_counts.get),
#             "start": current_start,
#             "end": last_note_time,
#             "duration": round(last_note_time - current_start, 4),
#         })

#     return groups
