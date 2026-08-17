"""Microphone recording with silence-based auto-stop."""

from __future__ import annotations

import wave
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
                print(f"[recorder] {status}")
            rms = float(np.sqrt(np.mean(np.square(indata.astype(np.float32)))))
            chunks.append(indata.copy())
            if rms >= cfg.silence_threshold:
                has_speech = True
                silent_run = 0
            elif has_speech:
                silent_run += 1

        with sd.InputStream(
            samplerate=cfg.sample_rate,
            channels=cfg.channels,
            dtype="int16",
            blocksize=frames_per_block,
            callback=callback,
        ):
            blocks = 0
            try:
                import sys

                print("🎤 Listening... (speak, then stay silent to stop)", file=sys.stderr)
                while blocks < max_blocks and (not has_speech or silent_run < silence_blocks):
                    import time

                    time.sleep(0.05)
                    blocks += 1
            except KeyboardInterrupt:
                pass

        if not chunks:
            raise RuntimeError("No audio captured.")

        audio = np.concatenate(chunks, axis=0)
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
