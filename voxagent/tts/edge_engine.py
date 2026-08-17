"""edge-tts engine — zero-setup fallback voice (needs internet for synthesis)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from ..config import VoxConfig
from .base import TTSEngine, register


@register
class EdgeTTSEngine(TTSEngine):
    name = "edge"

    def __init__(self, config: VoxConfig) -> None:
        try:
            import edge_tts  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "edge-tts is not installed. Run: pip install 'voxagent[local]'"
            ) from e
        self._voice = config.tts_voice
        self._rate = config.tts_rate

    def synthesize(self, text: str, out_path: str) -> str:
        import edge_tts

        async def _run() -> None:
            communicate = edge_tts.Communicate(text, self._voice, rate=self._rate)
            await communicate.save(out_path)

        asyncio.run(_run())
        return str(Path(out_path))
