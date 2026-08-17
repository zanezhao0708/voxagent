"""Minimal talk-loop demo without the MCP layer.

    python examples/demo_cli.py
"""

from voxagent.config import VoxConfig, load_dotenv


def main() -> None:
    load_dotenv()
    cfg = VoxConfig.from_env()
    print(f"STT: {cfg.stt_engine} | TTS: {cfg.tts_engine} | lang: {cfg.language}")

    from voxagent.stt import create_stt
    from voxagent.tts import create_tts

    stt = create_stt(cfg)
    tts = create_tts(cfg)

    while True:
        try:
            wav_path = "/tmp/vox_in.wav"
            import tempfile

            import sounddevice as sd
            from scipy.io import wavfile

            print("Press Enter to record (Ctrl+C to quit)...", end="", flush=True)
            input()
            print("Recording 5 seconds...")
            audio = sd.rec(int(5 * cfg.sample_rate), samplerate=cfg.sample_rate,
                           channels=cfg.channels, dtype="int16")
            sd.wait()
            wavfile.write(wav_path, cfg.sample_rate, audio)

            text = stt.transcribe(wav_path)
            print(f"You: {text}")
            if text:
                tts.synthesize(f"You said: {text}", "/tmp/vox_out.mp3")
                print("(audio written to /tmp/vox_out.mp3)")
        except KeyboardInterrupt:
            print("\nbye")
            return


if __name__ == "__main__":
    main()
