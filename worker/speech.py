import io
import os
import sys

import whisperx


def bucket_words_by_second(segments: list[dict]) -> list[dict]:
    """
    Flatten word-level timestamps across all segments and bucket them
    into 1-second windows.

    Returns a list of {"time": float, "words": str} dicts, one per
    1-second window that contains at least one word.
    """
    buckets: dict[int, list[str]] = {}

    for segment in segments:
        for word_info in segment.get("words", []):
            # Some words can lack timing if alignment failed for them
            if "start" not in word_info:
                continue
            # which 1s window it falls in
            bucket_index = int(word_info["start"])
            buckets.setdefault(bucket_index, []).append(word_info["word"])

    result = []
    for bucket_index in sorted(buckets):
        result.append({
            "time": float(bucket_index),
            "words": " ".join(buckets[bucket_index]),
        })

    return result


def _configure_windows_dll_paths() -> None:
    """On Windows, make sure CUDA/cuDNN DLLs bundled with pip packages
    are discoverable by whisperx/ctranslate2."""
    if sys.platform != "win32":
        return

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


def transcribe_audio(
    audio_buffer: io.BytesIO,
    device: str = "cuda",
    model_name: str = "large-v3",
    compute_type: str = "float16",
    language: str = "en",
    batch_size: int = 16,
    chunk_size: int = 30,
    vad_options: dict | None = None,
) -> list[dict]:
    """
    Transcribe and word-align an audio file with whisperx.

    Returns the list of aligned segments, each a dict with at least
    'start', 'end', and 'text' keys.
    """
    _configure_windows_dll_paths()

    if vad_options is None:
        vad_options = {
            "onset": 0.40,
            "offset": 0.35,
            "min_speech_duration_amount": 0.1,
            "speech_pad_duration_amount": 0.40,
        }

    model = whisperx.load_model(
        model_name, device, compute_type=compute_type, vad_options=vad_options)

    audio_buffer.seek(0)
    audio = whisperx.load_audio(audio_buffer)

    result = model.transcribe(
        audio,
        batch_size=batch_size,
        language=language,
        chunk_size=chunk_size,
    )

    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"], device=device)
    aligned_result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    return bucket_words_by_second(aligned_result["segments"])
