"""Smoke tests — run anywhere, no audio hardware or heavy deps needed."""

import pytest

from voxagent.config import VoxConfig


def test_config_defaults():
    cfg = VoxConfig()
    assert cfg.stt_engine == "whisper"
    assert cfg.tts_engine == "edge"
    assert cfg.sample_rate == 16000


def test_stt_registry_contains_whisper():
    import voxagent.stt  # noqa: F401  (imports populate the registry)
    from voxagent.stt.base import _REGISTRY

    assert "whisper" in _REGISTRY


def test_tts_registry():
    import voxagent.tts  # noqa: F401
    from voxagent.tts.base import _REGISTRY

    assert "edge" in _REGISTRY
    assert "cosyvoice" in _REGISTRY


# ---------------------------------------------------------------------- PTT


def _require_pynput():
    """Skip unless pynput imports (fails headless without X on Linux)."""
    try:
        import pynput  # noqa: F401
    except Exception as e:  # pynput raises non-ImportError headless
        pytest.skip(f"pynput unavailable here: {e.__class__.__name__}")


def test_parse_hotkey_single_char():
    _require_pynput()
    from voxagent.ptt import parse_hotkey

    tokens = parse_hotkey("j")
    assert len(tokens) == 1
    assert tokens[0] == "j"


def test_parse_hotkey_rejects_unknown():
    _require_pynput()

    from voxagent.ptt import parse_hotkey

    with pytest.raises(ValueError):
        parse_hotkey("banana")


def test_combo_tracker_char_keys():
    _require_pynput()
    from pynput import keyboard

    from voxagent.ptt import _ComboTracker

    tracker = _ComboTracker([keyboard.Key.ctrl, "j"])
    assert not tracker.is_complete()
    assert tracker.press(keyboard.KeyCode.from_char("j"))
    assert not tracker.is_complete()  # ctrl still missing
    assert tracker.press(keyboard.Key.ctrl)
    assert tracker.is_complete()
    # releasing one member breaks the combo
    assert tracker.release(keyboard.Key.ctrl)
    assert not tracker.is_complete()
    # re-press completes again without duplicate issues
    assert tracker.press(keyboard.Key.ctrl)
    assert tracker.is_complete()


def test_combo_tracker_space():
    _require_pynput()
    from pynput import keyboard

    from voxagent.ptt import _ComboTracker

    tracker = _ComboTracker([keyboard.Key.space])
    assert tracker.press(keyboard.Key.space)
    assert tracker.is_complete()


# --------------------------------------------------------------------- CLI


def test_cli_registers_ptt(capsys):
    _require_pynput()
    from voxagent.cli import main

    with pytest.raises(SystemExit) as e:
        main(["ptt", "--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "--hotkey" in out
    assert "--send" in out


def test_cli_doctor_runs():
    from voxagent.cli import main

    # doctor never raises; exit code may be 0 or 1 depending on env
    try:
        main(["doctor"])
    except SystemExit as e:
        assert e.code in (0, 1)


# ------------------------------------------------------------------ config


def test_load_dotenv_strips_inline_comments(tmp_path, monkeypatch):
    import os

    from voxagent.config import load_dotenv

    env = tmp_path / ".env"
    env.write_text(
        "VOX_TEST_ENGINE=edge          # inline note\n"
        "VOX_TEST_QUOTED='a # b'\n"
        "# full-line comment\n"
    )
    monkeypatch.delenv("VOX_TEST_ENGINE", raising=False)
    monkeypatch.delenv("VOX_TEST_QUOTED", raising=False)
    load_dotenv(str(env))
    assert os.environ["VOX_TEST_ENGINE"] == "edge"
    assert os.environ["VOX_TEST_QUOTED"] == "a # b"


def test_from_env_silence_default_matches_dataclass(monkeypatch):
    monkeypatch.delenv("VOXAGENT_SILENCE_MS", raising=False)
    assert VoxConfig.from_env().silence_ms == VoxConfig().silence_ms == 800


# ----------------------------------------------------------------- engines


def test_create_stt_none_and_unknown():
    from voxagent.stt import create_stt

    assert create_stt(VoxConfig(stt_engine="none")).transcribe("x") == "[STT disabled]"
    with pytest.raises(ValueError):
        create_stt(VoxConfig(stt_engine="nope"))


def test_create_tts_none_and_unknown():
    from voxagent.tts import create_tts

    assert create_tts(VoxConfig(tts_engine="none")).synthesize("hi", "/tmp/x") == ""
    with pytest.raises(ValueError):
        create_tts(VoxConfig(tts_engine="nope"))


def test_resolve_model_ref_local_cache(tmp_path, monkeypatch):
    import voxagent.stt.whisper_engine as we

    cache = tmp_path / ".voxagent" / "models"
    (cache / "small").mkdir(parents=True)
    (cache / "small" / "model.bin").write_bytes(b"x")
    monkeypatch.setattr(we.Path, "home", lambda: tmp_path)

    # exact cached size wins
    assert we.WhisperEngine._resolve_model_ref("small") == str(cache / "small")
    # missing size falls back to the largest cached one
    assert we.WhisperEngine._resolve_model_ref("base") == str(cache / "small")
    # non-alias paths pass through untouched
    assert we.WhisperEngine._resolve_model_ref("/custom/path") == "/custom/path"
