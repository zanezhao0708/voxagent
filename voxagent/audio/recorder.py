"""Microphone recording with silence-based auto-stop."""

from __future__ import annotations

import sys
import threading
import time
import wave
from collections.abc import Callable
from pathlib import Path

from ..config import VoxConfig


class Recorder:
    def __init__(self, config: VoxConfig) -> None:
        try:
            import sounddevice  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "sounddevice is not installed. Run: pip install 'voxagent[local]' "
                "(on Linux you may also need libportaudio2)"
            ) from e
        self._config = config

    def record_to_wav(self, out_path: str) -> str:
        """Record from the default microphone; stop on silence or max duration."""
        return self._record(out_path, stop_check=None)

    def record_until(self, active: threading.Event, out_path: str) -> str:
        """Record while `active` is set (push-to-talk mode).

        Returns after the event clears, or the max duration is reached —
        whichever comes first.
        """
        return self._record(out_path, stop_check=lambda: not active.is_set())

    def _record(self, out_path: str, stop_check: Callable[[], bool] | None = None) -> str:
        import numpy as np
        import sounddevice as sd

        cfg = self._config
        frames_per_block = int(cfg.sample_rate * 0.05)  # 50 ms blocks
        silence_blocks = max(1, cfg.silence_ms // 50)
        max_blocks = cfg.max_recording_s * 1000 // 50

        chunks: list[np.ndarray] = []
        silent_run = 0
        has_speech = False

        def callback(indata, _frames, _time, status):
            nonlocal silent_run, has_speech
            if status:
                print(f"[recorder] {status}", file=sys.stderr)
            # Normalize to [-1, 1] so the silence threshold (default 0.01)
            # means the same thing regardless of the int16 sample scale.
            mono = indata.astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(np.square(mono))))
            chunks.append(indata.copy())
            if rms >= cfg.silence_threshold:
                has_speech = True
                silent_run = 0
            elif has_speech:
                silent_run += 1

        hint = "hold the hotkey to talk" if stop_check else "speak, then stay silent to stop"
        print(f"🎤 Recording... ({hint})", file=sys.stderr)

        with sd.InputStream(
            samplerate=cfg.sample_rate,
            channels=cfg.channels,
            dtype="int16",
            blocksize=frames_per_block,
            callback=callback,
        ):
            blocks = 0
            # Give up if nothing above the noise floor after this many blocks,
            # so a missed threshold never means a full max-duration hang.
            no_speech_timeout_blocks = 10 * 1000 // 50  # 10s
            try:
                while blocks < max_blocks:
                    if stop_check is not None:
                        if stop_check():
                            break
                    elif has_speech and silent_run >= silence_blocks:
                        break
                    elif not has_speech and blocks >= no_speech_timeout_blocks:
                        print(
                            "[recorder] no speech detected, skipping",
                            file=sys.stderr,
                        )
                        break
                    time.sleep(0.05)
                    blocks += 1
            except KeyboardInterrupt:
                pass

        if not chunks:
            raise RuntimeError("No audio captured.")

        audio = np.concatenate(chunks, axis=0)
        if not has_speech:
            # Nothing meaningful was said; return an empty-but-valid file so
            # callers can surface "[nothing heard]" cleanly.
            audio = audio[: int(cfg.sample_rate * 0.1)]
        return self._write_wav(out_path, audio, cfg.sample_rate, cfg.channels)

    @staticmethod
    def _write_wav(path: str, audio, sample_rate: int, channels: int) -> str:
        path = str(Path(path))
        with wave.open(path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # int16
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
        return path
