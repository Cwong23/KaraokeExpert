import os
import sys

import whisperx


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
    audio_file: str,
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
    audio = whisperx.load_audio(audio_file)

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

    return aligned_result["segments"]


if __name__ == "__main__":
