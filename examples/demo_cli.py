"""Minimal talk-loop demo without the MCP layer.

    pip install 'voxagent[local]'
    python examples/demo_cli.py

Speak after pressing Enter; recording stops automatically when you pause.
"""

from voxagent.config import VoxConfig, load_dotenv


def main() -> None:
    load_dotenv()
    cfg = VoxConfig.from_env()
    print(f"STT: {cfg.stt_engine} | TTS: {cfg.tts_engine} | lang: {cfg.language}")

    from voxagent.audio import Recorder, play_file
    from voxagent.stt import create_stt
    from voxagent.tts import create_tts

    stt = create_stt(cfg)
    tts = create_tts(cfg)
    recorder = Recorder(cfg)

    wav_path = "/tmp/vox_in.wav"
    out_path = "/tmp/vox_out.mp3"

    while True:
        try:
            print("Press Enter to record (speak, pause to stop; Ctrl+C to quit)...",
                  end="", flush=True)
            input()
            recorder.record_to_wav(wav_path)

            text = stt.transcribe(wav_path)
            print(f"You: {text}")
            if text:
                tts.synthesize(f"You said: {text}", out_path)
                play_file(out_path)
        except KeyboardInterrupt:
            print("\nbye")
            return


if __name__ == "__main__":
    main()
