"""Configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

_TRUE = {"1", "true", "yes", "on"}


def _get(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()


@dataclass
class VoxConfig:
    # STT
    stt_engine: str = "whisper"
    whisper_model: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"

    # TTS
    tts_engine: str = "edge"  # edge | cosyvoice | none
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_rate: str = "+0%"
    cosyvoice_base_url: str = "http://127.0.0.1:9880"

    # Conversation
    language: str = "auto"  # auto | zh | en | ...

    # Recorder
    sample_rate: int = 16000
    channels: int = 1
    silence_ms: int = 800
    silence_threshold: float = 0.01
    max_recording_s: int = 60

    @classmethod
    def from_env(cls) -> VoxConfig:
        return cls(
            stt_engine=_get("VOXAGENT_STT_ENGINE", "whisper").lower(),
            whisper_model=_get("WHISPER_MODEL", "small"),
            whisper_device=_get("WHISPER_DEVICE", "auto"),
            whisper_compute_type=_get("WHISPER_COMPUTE_TYPE", "auto"),
            tts_engine=_get("VOXAGENT_TTS_ENGINE", "edge").lower(),
            tts_voice=_get("TTS_VOICE", "zh-CN-XiaoxiaoNeural"),
            tts_rate=_get("TTS_RATE", "+0%"),
            cosyvoice_base_url=_get("COSYVOICE_BASE_URL", "http://127.0.0.1:9880"),
            language=_get("VOXAGENT_LANGUAGE", "auto"),
            sample_rate=int(_get("VOXAGENT_SAMPLE_RATE", "16000")),
            channels=int(_get("VOXAGENT_CHANNELS", "1")),
            silence_ms=int(_get("VOXAGENT_SILENCE_MS", "1200")),
            silence_threshold=float(_get("VOXAGENT_SILENCE_THRESHOLD", "0.01")),
            max_recording_s=int(_get("VOXAGENT_MAX_RECORDING_S", "60")),
        )


def load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader (no external dependency)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if value and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            os.environ.setdefault(key, value)
