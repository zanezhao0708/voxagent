"""TTS engine abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from ..config import VoxConfig


class TTSEngine(ABC):
    """A text-to-speech engine."""

    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str, out_path: str) -> str:
        """Synthesize `text` to an audio file (WAV) and return the path."""
        raise NotImplementedError


_REGISTRY: dict[str, Callable[[VoxConfig], TTSEngine]] = {}


def register(engine_cls: type[TTSEngine]) -> type[TTSEngine]:
    _REGISTRY[engine_cls.name] = engine_cls
    return engine_cls


def create_tts(config: VoxConfig) -> TTSEngine:
    if config.tts_engine == "none":
        class _Muted(TTSEngine):
            name = "none"

            def synthesize(self, text: str, out_path: str) -> str:
                return ""  # voice off

        return _Muted()
    if config.tts_engine not in _REGISTRY:
        raise ValueError(
            f"Unknown TTS engine '{config.tts_engine}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[config.tts_engine](config)
