"""CosyVoice engine — talks to a local CosyVoice API server for high-quality
offline Chinese/multilingual voices.

Start the server first, e.g.:
    git clone https://github.com/FunAudioLLM/CosyVoice && cd CosyVoice
    python api.py  # serves http://127.0.0.1:9880
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from ..config import VoxConfig
from .base import TTSEngine, register


@register
class CosyVoiceEngine(TTSEngine):
    name = "cosyvoice"

    def __init__(self, config: VoxConfig) -> None:
        self._base_url = config.cosyvoice_base_url.rstrip("/")

    def synthesize(self, text: str, out_path: str) -> str:
        payload = json.dumps({"text": text}).encode("utf-8")
        request = urllib.request.Request(
            f"{self._base_url}/tts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            audio = response.read()
        Path(out_path).write_bytes(audio)
        return str(Path(out_path))
