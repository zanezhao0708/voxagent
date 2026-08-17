<div align="center">

# 🎙️ VoxAgent

**Talk to your coding agent. It talks back.**

Local-first voice I/O for Claude Code, Cursor, OpenClaw and any MCP client.

[![CI](https://github.com/zanezhao0708/voxagent/actions/workflows/ci.yml/badge.svg)](https://github.com/zanezhao0708/voxagent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![MCP](https://img.shields.io/badge/transport-MCP-black.svg)](https://modelcontextprotocol.io)

[English](README.md) · [简体中文](README_ZH.md)

</div>

![VoxAgent demo](docs/demo.svg)

## Why

Coding agents went from autocomplete to coworkers — but the interface is still
a keyboard. VoxAgent gives your agent **ears and a mouth**:

- 🎤 **`listen()`** — dictate instructions, code snippets, or code review feedback
- 🔊 **`speak()`** — spoken progress updates; go get coffee while your agent talks
- 🗣️ **`ask_user()`** — the agent asks, you answer out loud from across the room
- 🕹️ **Push-to-talk** — hold a global hotkey anywhere; your words go straight
  into `claude -p`, and the reply is spoken back

Everything runs **on your machine**. STT is fully offline (faster-whisper);
TTS starts with a zero-setup voice and upgrades to a local CosyVoice server
for production-quality speech. No API keys required.

## Quickstart

```bash
pip install 'voxagent[local]'
voxagent doctor        # check mic + deps
voxagent demo          # try the talk-loop standalone

# Register with Claude Code
claude mcp add voxagent -- voxagent serve

# Enable the agent skill (when to speak, how to behave)
mkdir -p ~/.claude/skills && cp -r skills/voice-control ~/.claude/skills/

# Push-to-talk daemon (optional): talk to Claude Code from any app
pip install 'voxagent[ptt]'
voxagent ptt --send 'claude -p'
```

Then just say: **"voice mode on"** — or hold the PTT hotkey (default
`Ctrl+Shift+Space`) and talk.

Works with any MCP client — Cursor, OpenClaw, Codex and friends all speak MCP.

## Architecture

```
        ┌─────────────┐     MCP (stdio)      ┌──────────────────┐
 mic ──▶│   listen()  │◀────────────────────▶│  Claude Code /   │
        │  (STT)      │                      │  Cursor / any    │
 spk ◀──│   speak()   │◀────────────────────▶│  MCP client      │
        │  (TTS)      │      tools+skill     └──────────────────┘
        └─────────────┘
          faster-whisper   edge-tts / CosyVoice (pluggable)
          ▲ fully offline           ▲ swap via env var
```

**Engines are pluggable** — set one env var to swap either side:

| Layer | Default | Upgrade path | Config |
| --- | --- | --- | --- |
| STT | faster-whisper (`small`) | `medium` / `large-v3`, GPU | `WHISPER_MODEL`, `WHISPER_DEVICE` |
| TTS | edge-tts (zero setup) | local CosyVoice server | `VOXAGENT_TTS_ENGINE=cosyvoice` |
| Language | auto-detect | pin `zh` / `en` / ... | `VOXAGENT_LANGUAGE` |

See [.env.example](.env.example) for all options.

## MCP Tools

| Tool | What it does |
| --- | --- |
| `listen()` | Record mic → transcript. Silence auto-stop, VAD filtered. |
| `speak(text)` | Text → speech on your speakers. Returns seconds spoken. |
| `ask_user(question)` | Speak a question, then capture the spoken answer. |

The bundled **Agent Skill** (`skills/voice-control`) teaches the agent *when*
to use them: short spoken replies, voice announcements before long tasks,
language mirroring, graceful fallback to text.

## Troubleshooting

**Model download fails** (network errors from huggingface.co): download the
model manually from a mirror, then point `WHISPER_MODEL` at the folder:

```bash
bash scripts/download_model.sh tiny            # or base / small
export WHISPER_MODEL="$HOME/.voxagent/models/tiny"
```

The script pulls from hf-mirror.com with plain `curl`, bypassing the
huggingface_hub SDK entirely. Alternatively, set `HF_ENDPOINT=https://hf-mirror.com`
and `HF_HUB_DISABLE_XET=1` before running if the SDK works for you.

**Holding the hotkey types characters into the focused app** (e.g. `ctrl+j`
sends newlines in a terminal, scrolling it while you speak): on macOS the
daemon swallows the hotkey's character key while the combo is held. If the
suppressor is unavailable, prefer a character-free hotkey such as
`--hotkey f6` or `--hotkey ctrl+cmd+j`.

**macOS hotkeys don't respond**: grant your terminal *Accessibility / Input
Monitoring* permission in System Settings → Privacy & Security, then restart
the daemon.

## Roadmap

- [x] Push-to-talk global hotkey (`voxagent ptt`)
- [ ] Streaming STT (partial transcripts while you speak)
- [ ] Voice memory — clone your own voice for agent replies
- [ ] OpenClaw / n8n integration recipes
- [ ] Docker image with bundled CosyVoice

## Contributing

Issues and PRs welcome — especially new engine adapters (GPT-SoVITS, F5-TTS,
Piper...). Each adapter is ~40 lines; see `voxagent/tts/cosyvoice_engine.py`
for the pattern.

## License

[MIT](LICENSE)
