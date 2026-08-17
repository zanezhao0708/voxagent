"""STT engine abstraction. Engines are registered lazily so that heavy
dependencies (faster-whisper) are only imported when actually used."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from ..config import VoxConfig


class STTEngine(ABC):
    """A speech-to-text engine."""

    name: str = "base"

    @abstractmethod
    def transcribe(self, wav_path: str, language: str | None = None) -> str:
        """Transcribe a 16-bit PCM WAV file and return plain text."""
        raise NotImplementedError


_REGISTRY: dict[str, Callable[[VoxConfig], STTEngine]] = {}


def register(engine_cls: type[STTEngine]) -> type[STTEngine]:
    _REGISTRY[engine_cls.name] = engine_cls
    return engine_cls


def create_stt(config: VoxConfig) -> STTEngine:
    if config.stt_engine == "none":
        class _Disabled(STTEngine):
            name = "none"

            def transcribe(self, wav_path: str, language: str | None = None) -> str:
                return "[STT disabled]"

        return _Disabled()
    if config.stt_engine not in _REGISTRY:
        raise ValueError(
            f"Unknown STT engine '{config.stt_engine}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[config.stt_engine](config)
