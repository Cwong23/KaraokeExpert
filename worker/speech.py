import io
import os
import sys

import whisperx
import tempfile


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
            if "start" not in word_info:
                continue
            bucket_index = int(word_info["start"])
            buckets.setdefault(bucket_index, []).append(word_info["word"])

    # Flatten all words in order first, then apply punctuation
    ordered_buckets = sorted(buckets)
    all_words: list[tuple[int, str]] = []  # (bucket_index, word)
    for bucket_index in ordered_buckets:
        for word in buckets[bucket_index]:
            all_words.append((bucket_index, word))

    # Insert periods before capitalized words (except the very first word)
    for i in range(1, len(all_words)):
        word = all_words[i][1]
        if word and word[0].isupper():
            prev_bucket, prev_word = all_words[i - 1]
            # Add period to the previous word if it doesn't already have punctuation
            if prev_word and prev_word[-1] not in ".!?,;:":
                all_words[i - 1] = (prev_bucket, prev_word + ".")

    # Re-bucket the modified words
    result_buckets: dict[int, list[str]] = {}
    for bucket_index, word in all_words:
        result_buckets.setdefault(bucket_index, []).append(word)

    result = []
    for bucket_index in sorted(result_buckets):
        result.append({
            "time": float(bucket_index),
            "words": " ".join(result_buckets[bucket_index]),
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
    """
    _configure_windows_dll_paths()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_buffer.read())
        tmp_path = tmp.name

    if vad_options is None:
        vad_options = {
            "onset": 0.40,
            "offset": 0.35,
            "min_speech_duration_amount": 0.1,
            "speech_pad_duration_amount": 0.40,
        }

    model = whisperx.load_model(
        model_name, device, compute_type=compute_type, vad_options=vad_options)

    audio = whisperx.load_audio(tmp_path)

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
