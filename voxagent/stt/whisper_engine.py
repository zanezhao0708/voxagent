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

        device = None if config.whisper_device == "auto" else config.whisper_device
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
