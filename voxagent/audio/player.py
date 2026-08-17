"""Play audio files through the default output device."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


def play_file(path: str) -> bool:
    """Play any audio file via an available OS player. True if it ran.

    Player flags differ per binary; ffplay/mpv need no-display flags while
    afplay (macOS) takes none of them.
    """
    if not path or not Path(path).exists():
        return False
    for binary in ("ffplay", "mpv", "afplay"):
        player = shutil.which(binary)
        if not player:
            continue
        if binary == "ffplay":
            args = [player, "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        elif binary == "mpv":
            args = [player, "--no-video", "--really-quiet", path]
        else:  # afplay
            args = [player, path]
        try:
            subprocess.run(args, check=False)
            return True
        except OSError:
            continue
    return False


def play_wav(path: str) -> float:
    """Play a WAV file. Returns duration in seconds (0 if muted/missing)."""
    if not path or not Path(path).exists():
        return 0.0
    try:
        import sounddevice as sd
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "sounddevice is not installed. Run: pip install 'voxagent[local]'"
        ) from e

    with wave.open(str(path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()

    import numpy as np

    dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(width)
    if dtype is None:
        raise ValueError(f"Unsupported sample width: {width}")
    audio = np.frombuffer(frames, dtype=dtype)
    if channels > 1:
        audio = audio.reshape(-1, channels)
    sd.play(audio, rate, blocking=True)
    return len(audio) / channels / rate
