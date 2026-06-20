import os
import sys

# Windows DLL environment resolution safety
if sys.platform == "win32":
    for path in sys.path:
        if "site-packages" in path:
            cublas_bin = os.path.join(path, "nvidia", "cublas", "bin")
            cudnn_bin = os.path.join(path, "nvidia", "cudnn", "bin")
            if os.path.exists(cublas_bin) and os.path.exists(cudnn_bin):
                os.environ["PATH"] = f"{cublas_bin};{cudnn_bin};" + \
                    os.environ["PATH"]
                os.add_dll_directory(cublas_bin)
                os.add_dll_directory(cudnn_bin)
            break

import whisperx

device = "cuda"
audio_file = "output_stems/vocals.wav"

# 1. Tweak VAD parameters to handle singing dynamics
vad_options = {
    # Lower onset threshold makes it more sensitive to fast, aggressive vocal starts
    "onset": 0.40,
    "offset": 0.35,          # Keeps the frame open longer during trailing vocal runs
    "min_speech_duration_amount": 0.1,
    # Adds aggressive padding around vocal blocks so lyrics aren't clipped
    "speech_pad_duration_amount": 0.40
}

print("Loading WhisperX model...")
model = whisperx.load_model(
    "large-v3", device, compute_type="float16", vad_options=vad_options)

print("Transcribing isolated vocals...")
audio = whisperx.load_audio(audio_file)

# 2. Force decoding parameters tuned for musical structures
result = model.transcribe(
    audio,
    batch_size=16,
    # Force English to avoid false language shifts on vocal riffs
    language="en",
    chunk_size=30,
)

# 3. Use phonetic alignment to lock timestamps tightly to the beat
print("Aligning phonemes...")
model_a, metadata = whisperx.load_align_model(
    language_code=result["language"], device=device)
aligned_result = whisperx.align(
    result["segments"],
    model_a,
    metadata,
    audio,
    device,
    return_char_alignments=False
)

# Output results cleanly
for segment in aligned_result["segments"]:
    print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
