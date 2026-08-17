"""VoxAgent command line interface.

    voxagent serve   run the MCP server (stdio)
    voxagent demo    local talk-loop demo (no agent required)
    voxagent doctor  check environment and dependencies
"""

from __future__ import annotations

import argparse
import sys


def _cmd_serve(_args) -> int:
    from .server import main as serve_main

    serve_main()
    return 0


def _cmd_demo(_args) -> int:
    from .config import VoxConfig, load_dotenv

    load_dotenv()
    cfg = VoxConfig.from_env()
    from .audio import Recorder, play_wav
    from .stt import create_stt
    from .tts import create_tts

    stt = create_stt(cfg)
    tts = create_tts(cfg)
    recorder = Recorder(cfg)

    print("VoxAgent demo — Ctrl+C to exit.")
    while True:
        try:
            wav = "/tmp/voxagent_demo_in.wav"
            out = "/tmp/voxagent_demo_out.mp3"
            recorder.record_to_wav(wav)
            text = stt.transcribe(wav)
            print(f"🧑 You said: {text}")
            if not text:
                continue
            path = tts.synthesize(f"You said: {text}", out)
            try:
                play_wav(path)
            except Exception:
                pass
        except KeyboardInterrupt:
            print("\nBye!")
            return 0


def _cmd_ptt(args) -> int:
    from .config import VoxConfig, load_dotenv
    from .ptt import PushToTalkDaemon

    load_dotenv()
    cfg = VoxConfig.from_env()
    PushToTalkDaemon(
        cfg,
        hotkey=args.hotkey,
        send_to=args.send,
        speak_reply=not args.no_speak_reply,
    ).run()
    return 0


def _cmd_doctor(_args) -> int:
    from importlib.util import find_spec

    checks = {
        "mcp": find_spec("mcp") is not None,
        "faster-whisper": find_spec("faster_whisper") is not None,
        "sounddevice": find_spec("sounddevice") is not None,
        "numpy": find_spec("numpy") is not None,
        "edge-tts": find_spec("edge_tts") is not None,
    }
    ok = True
    for name, present in checks.items():
        mark = "✅" if present else "❌"
        print(f"{mark} {name}")
        if not present and name not in {"faster-whisper", "sounddevice", "numpy", "edge-tts"}:
            ok = False
    if not all(checks.values()):
        print("\nMissing optional deps? Run: pip install 'voxagent[local]'")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="voxagent", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("serve", help="run the MCP server (stdio)")
    sub.add_parser("demo", help="local talk-loop demo")
    sub.add_parser("doctor", help="check environment and dependencies")
    ptt = sub.add_parser("ptt", help="global push-to-talk hotkey daemon")
    ptt.add_argument("--hotkey", default="ctrl+shift+space", help="e.g. ctrl+shift+space")
    ptt.add_argument(
        "--send",
        default=None,
        help='pipe transcript to a command, e.g. "claude -p" (default: print only)',
    )
    ptt.add_argument("--no-speak-reply", action="store_true")

    args = parser.parse_args(argv)
    handler = {
        "serve": _cmd_serve,
        "demo": _cmd_demo,
        "doctor": _cmd_doctor,
        "ptt": _cmd_ptt,
    }[args.command]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
