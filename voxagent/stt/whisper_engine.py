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
        compute = (
            "default" if config.whisper_compute_type == "auto" else config.whisper_compute_type
        )
        self._model = WhisperModel(config.whisper_model, device=device, compute_type=compute)
        self._default_language = None if config.language == "auto" else config.language

    def transcribe(self, wav_path: str, language: str | None = None) -> str:
        segments, _info = self._model.transcribe(
            str(Path(wav_path)),
            language=language or self._default_language,
            vad_filter=True,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
