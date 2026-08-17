"""Push-to-talk daemon — global hotkey voice input for your terminal agent.

Hold the hotkey, speak, release: your words are transcribed and (optionally)
piped straight into Claude Code, whose reply is spoken back to you.

    voxagent ptt                       # transcribe to stdout
    voxagent ptt --send 'claude -p'    # pipe to Claude Code, speak the reply
    voxagent ptt --hotkey ctrl+shift+space

Requires: pip install 'voxagent[ptt]'
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import VoxConfig, load_dotenv


def _macos_input_trusted() -> bool:
    """Whether macOS permits this app to monitor global input events.

    Always True off macOS; if the probe itself fails, assume True rather
    than blocking users spuriously (pynput will warn on its own).
    """
    if sys.platform != "darwin":
        return True
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore

        return bool(AXIsProcessTrusted())
    except Exception:
        return True

# --------------------------------------------------------------- hotkey utils


def parse_hotkey(spec: str) -> list[str]:
    """Parse 'ctrl+shift+space' into a list of normalized key tokens.

    Returned tokens mix pynput Key objects (modifiers) and single-char strings
    (letters/space handled by char comparison downstream).
    """
    from pynput import keyboard

    mapping = {
        "ctrl": keyboard.Key.ctrl,
        "ctrl_l": keyboard.Key.ctrl_l,
        "ctrl_r": keyboard.Key.ctrl_r,
        "alt": keyboard.Key.alt,
        "altgr": keyboard.Key.alt_gr,
        "shift": keyboard.Key.shift,
        "shift_l": keyboard.Key.shift_l,
        "shift_r": keyboard.Key.shift_r,
        "cmd": keyboard.Key.cmd,
        "cmd_l": keyboard.Key.cmd_l,
        "super": keyboard.Key.cmd,
        "win": keyboard.Key.cmd,
        "space": keyboard.Key.space,
        "esc": keyboard.Key.esc,
        "tab": keyboard.Key.tab,
    }
    tokens: list[object] = []
    for part in spec.strip().strip("<>").split("+"):
        name = part.strip().lower()
        if not name:
            continue
        if len(name) == 1:
            tokens.append(name)
        elif name in mapping:
            tokens.append(mapping[name])
        else:
            raise ValueError(f"Unknown hotkey part: {part!r}")
    if not tokens:
        raise ValueError(f"Empty hotkey spec: {spec!r}")
    return tokens


@dataclass
class _ComboTracker:
    """Tracks which combo members are currently held."""

    tokens: list[object]
    pressed: set = field(default_factory=set)

    def press(self, key) -> bool:
        """Record a key press. Returns True if the combo became complete."""
        for token in self.tokens:
            if _matches(token, key):
                self.pressed.add(token)
        return self.is_complete()

    def release(self, key) -> bool:
        """Record a key release. Returns True if the combo just broke."""
        broken = False
        for token in list(self.pressed):
            if _matches(token, key):
                self.pressed.discard(token)
                broken = True
        return broken

    def is_complete(self) -> bool:
        return len(self.pressed) >= len(self.tokens)


def _matches(token, key) -> bool:
    if isinstance(token, str):
        return bool(getattr(key, "char", None)) and key.char.lower() == token
    # Key.space reports char ' ' on some platforms, Key.space on others
    if getattr(key, "char", None) == " " and token.__class__.__name__ == "Key":
        return token.name == "space" if hasattr(token, "name") else False
    return key == token


# -------------------------------------------------------------------- daemon


class PushToTalkDaemon:
    """Hold-to-talk loop: hotkey down → record; hotkey up → transcribe → act."""

    def __init__(
        self,
        config: VoxConfig,
        hotkey: str = "ctrl+shift+space",
        send_to: str | None = None,
        speak_reply: bool = True,
        print_fn: Callable[[str], None] = print,
    ) -> None:
        try:
            from pynput import keyboard  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "pynput is not installed. Run: pip install 'voxagent[ptt]' "
                "(on Linux/Wayland global hotkeys may need extra setup)"
            ) from e

        from .audio import Recorder
        from .stt import create_stt
        from .tts import create_tts

        self._config = config
        self._stt = create_stt(config)
        self._tts = create_tts(config)
        self._recorder = Recorder(config)
        self._hotkey_spec = hotkey
        self._send_to = send_to
        self._speak_reply = speak_reply
        self._print = print_fn
        self._stop = threading.Event()
        self._recording = threading.Event()

    # ------------------------------------------------------------------ API

    def run(self) -> None:  # pragma: no cover — needs a real desktop session
        from pynput import keyboard

        if not _macos_input_trusted():
            self._print(
                "❌ macOS is blocking global hotkeys for this terminal app.\n"
                "   Fix:\n"
                "     1. System Settings → Privacy & Security → Accessibility\n"
                "     2. Enable the app you launch voxagent from (Terminal / iTerm2 ...)\n"
                "     3. Fully quit that app (Cmd+Q) and reopen it\n"
                "     4. Run `voxagent ptt` again\n"
                "   Without this, the hotkey will never fire — exactly the\n"
                "   'This process is not trusted!' warning you may have seen."
            )
            raise SystemExit(1)

        tracker = _ComboTracker(parse_hotkey(self._hotkey_spec))

        def on_press(key):
            try:
                if tracker.press(key) and not self._recording.is_set():
                    self._recording.set()
                    threading.Thread(target=self._record_and_handle, daemon=True).start()
            except Exception as e:  # never kill the listener
                self._print(f"[ptt] {e}")

        def on_release(key):
            try:
                if tracker.release(key):
                    self._recording.clear()  # worker sees this and stops
            except Exception as e:
                self._print(f"[ptt] {e}")

        self._print(
            f"🎙️  Push-to-talk ready. Hold [{self._hotkey_spec}], speak, release."
        )
        if self._send_to:
            self._print(f"   Transcripts are piped to: {self._send_to}")
        self._print("   Ctrl+C to quit.")

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            try:
                listener.wait()
                threading.Event().wait()
            except KeyboardInterrupt:
                self._print("\nBye!")
                self._stop.set()

    # ------------------------------------------------------------- internals

    def _record_and_handle(self) -> None:
        wav_path = tempfile.mktemp(suffix=".wav")
        try:
            self._recorder.record_until(self._recording, wav_path)
            if self._stop.is_set():
                return
            text = self._stt.transcribe(wav_path)
        except Exception as e:  # pragma: no cover
            self._print(f"[ptt] error: {e}")
            return
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        self._handle_transcript(text)

    def _handle_transcript(self, text: str) -> None:
        if not text.strip():
            self._print("[ptt] nothing heard")
            return
        self._print(f"\n🧑 {text}\n")
        if not self._send_to:
            return
        reply = self._send_prompt(text)
        self._print(f"🤖 {reply}\n")
        if self._speak_reply and reply and not reply.startswith("[ptt]"):
            self._speak(reply)

    def _send_prompt(self, text: str) -> str:
        cmd = [*shlex_split(self._send_to), text]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
            return out.stdout.strip()
        except FileNotFoundError:
            return f"[ptt] command not found: {cmd[0]}"
        except subprocess.CalledProcessError as e:
            return f"[ptt] exit {e.returncode}: {e.stderr.strip()[:200]}"
        except subprocess.TimeoutExpired:
            return "[ptt] command timed out (300s)"

    def _speak(self, text: str) -> None:
        try:
            out_path = tempfile.mktemp(suffix=".mp3")
            path = self._tts.synthesize(text, out_path)
            if not path:
                return
            try:
                from .audio import play_wav

                play_wav(path)
            except Exception:
                player = shutil.which("ffplay") or shutil.which("afplay") or shutil.which("mpv")
                if player:
                    subprocess.run([player, "-nodisp", "-autoexit", path], check=False)
        except Exception as e:  # pragma: no cover
            self._print(f"[ptt] tts failed: {e}")


def shlex_split(cmd: str) -> list[str]:
    import shlex

    return shlex.split(cmd)


def main() -> None:  # pragma: no cover — CLI entry
    import argparse

    parser = argparse.ArgumentParser(prog="voxagent ptt", description=__doc__)
    parser.add_argument("--hotkey", default="ctrl+shift+space")
    parser.add_argument(
        "--send",
        default=None,
        help="pipe transcript to a command, e.g. \"claude -p\" (default: print only)",
    )
    parser.add_argument("--no-speak-reply", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    cfg = VoxConfig.from_env()
    PushToTalkDaemon(
        cfg,
        hotkey=args.hotkey,
        send_to=args.send,
        speak_reply=not args.no_speak_reply,
    ).run()


if __name__ == "__main__":
    main()
