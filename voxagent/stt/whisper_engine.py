"""faster-whisper STT engine — fully offline, CPU friendly."""

from __future__ import annotations

from pathlib import Path

from ..config import VoxConfig
from .base import STTEngine, register


@register
class WhisperEngine(STTEngine):
    name = "whisper"

    def __init__(self, config: VoxConfig) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "faster-whisper is not installed. Run: pip install 'voxagent[local]'"
            ) from e

        # ctranslate2 requires a concrete device string; "auto" resolves to
        # cuda when actually available, else cpu.
        if config.whisper_device == "auto":
            try:
                import ctranslate2

                device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
            except Exception:
                device = "cpu"
        else:
            device = config.whisper_device
        if config.whisper_compute_type == "auto":
            # int8 is ~2x faster than float32 on CPU with negligible accuracy
            # loss for short voice commands; float16 is native on GPUs.
            compute = "float16" if device == "cuda" else "int8"
        else:
            compute = config.whisper_compute_type
        self._model = WhisperModel(config.whisper_model, device=device, compute_type=compute)
        self._default_language = None if config.language == "auto" else config.language

    def transcribe(self, wav_path: str, language: str | None = None) -> str:
        segments, _info = self._model.transcribe(
            str(Path(wav_path)),
            language=language or self._default_language,
            vad_filter=True,
            # beam_size=1: greedy decoding is several times faster than the
            # default beam search and plenty accurate for spoken commands.
            beam_size=1,
            condition_on_previous_text=False,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
