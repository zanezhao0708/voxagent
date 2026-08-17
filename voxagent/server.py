"""VoxAgent MCP server.

Exposes voice tools to any MCP client (Claude Code, Cursor, OpenClaw, ...):

    listen()            capture speech from the mic, return the transcript
    speak(text)         say something out loud, return seconds spoken
    ask_user(question)  speak a question, then listen for the answer

Run standalone:
    voxagent serve
Register with Claude Code:
    claude mcp add voxagent -- voxagent serve
"""

from __future__ import annotations

import tempfile
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .config import VoxConfig, load_dotenv

mcp = FastMCP("voxagent")

_config: Optional[VoxConfig] = None
_stt = None
_tts = None
_recorder = None


def _services():
    """Lazily build config + engines (heavy deps imported on first use)."""
    global _config, _stt, _tts, _recorder
    if _config is None:
        load_dotenv()
        _config = VoxConfig.from_env()
        from .stt import create_stt
        from .tts import create_tts

        _stt = create_stt(_config)
        _tts = create_tts(_config)
        from .audio import Recorder

        _recorder = Recorder(_config)
    return _config, _stt, _tts, _recorder


def _listen_once() -> str:
    cfg, stt, _tts, recorder = _services()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    recorder.record_to_wav(wav_path)
    try:
        return stt.transcribe(wav_path)
    finally:
        import os

        os.unlink(wav_path)


@mcp.tool()
def listen() -> str:
    """Record speech from the default microphone and return the transcript.

    Use this to hear the user: call it when the user asks to dictate, when a
    task needs verbal input, or as a hands-free way to receive the next
    instruction.
    """
    return _listen_once() or "[nothing heard]"


@mcp.tool()
def speak(text: str) -> str:
    """Say `text` out loud through the speakers. Returns seconds spoken.

    Keep spoken text short (1-2 sentences). Ideal for progress updates,
    asking a quick question, or reading a summary aloud while the user is
    away from the keyboard.
    """
    cfg, _stt, tts, _recorder = _services()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    try:
        audio_path = tts.synthesize(text, out_path)
        if not audio_path:
            return "0.0"
        from .audio import play_wav

        try:
            seconds = play_wav(audio_path)
        except Exception:
            # edge-tts produces mp3; fall back to system players
            import shutil
            import subprocess

            player = shutil.which("ffplay") or shutil.which("afplay") or shutil.which("mpv")
            if player:
                subprocess.run([player, "-nodisp", "-autoexit", audio_path], check=False)
                return "-1"
            raise
        return f"{seconds:.1f}"
    finally:
        import os

        os.unlink(out_path)


@mcp.tool()
def ask_user(question: str) -> str:
    """Ask the user a question out loud and wait for their spoken answer.

    Returns the transcript of what the user said. Use for quick confirmations
    or choices while working hands-free, e.g. ask_user('Run the tests now?').
    """
    speak(question)
    return _listen_once() or "[nothing heard]"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
