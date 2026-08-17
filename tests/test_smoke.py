"""Smoke tests — run anywhere, no audio hardware or heavy deps needed."""

from voxagent.config import VoxConfig


def test_config_defaults():
    cfg = VoxConfig()
    assert cfg.stt_engine == "whisper"
    assert cfg.tts_engine == "edge"
    assert cfg.sample_rate == 16000


def test_stt_registry_contains_whisper():
    from voxagent.stt.base import _REGISTRY

    import voxagent.stt  # noqa: F401  (imports populate the registry)

    assert "whisper" in _REGISTRY


def test_tts_registry():
    from voxagent.tts.base import _REGISTRY

    import voxagent.tts  # noqa: F401

    assert "edge" in _REGISTRY
    assert "cosyvoice" in _REGISTRY
