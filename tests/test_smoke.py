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
