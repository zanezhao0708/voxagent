# Launch Copy Pack (发布文案包)

Copy-paste ready posts for the v0.1.0 launch. Demo GIF lives at
`docs/demo.gif` in the repo — link the raw GitHub URL below.

---

## 1. Show HN

**Title:** Show HN: VoxAgent – Talk to your coding agent, it talks back

**Text:**

Hi HN, I built VoxAgent (https://github.com/zanezhao0708/voxagent) — a
local-first voice layer for coding agents like Claude Code, Cursor, or any
MCP client.

It gives your agent three tools: `listen()`, `speak(text)`, and
`ask_user(question)`. The killer combo is push-to-talk: hold a global hotkey
anywhere, speak, release — your words get piped into `claude -p` and the
reply is spoken back while you're across the room making coffee.

Why local-first: STT runs fully offline on faster-whisper. TTS starts with a
zero-setup voice (edge-tts) and swaps to a self-hosted CosyVoice server for
better quality. No API keys, no cloud dependency, MIT licensed.

There's also an Agent Skill that teaches the agent *when* to talk: short
spoken replies, a heads-up before long tasks, mirror the user's language,
fall back to text gracefully.

Would love feedback on the push-to-talk UX — especially from Wayland users,
global hotkeys there are still the wild west.

Demo GIF: [GIF]

---

## 2. Reddit r/LocalLLaMA

**Title:** VoxAgent: push-to-talk voice I/O for Claude Code / any MCP agent — fully local STT, MIT

**Body:**

I open-sourced a small bridge between your microphone and your coding agent.

- MCP server with `listen` / `speak` / `ask_user` tools
- Push-to-talk daemon: hold Ctrl+Shift+Space, speak, release → transcript
  goes to `claude -p`, reply is spoken back
- STT: faster-whisper, 100% offline (small model runs fine on CPU)
- TTS: edge-tts by default, or point it at a local CosyVoice API for
  high-quality Chinese/multilingual voices
- MIT license, Python 3.10+, ~40 lines per engine adapter if you want to add
  GPT-SoVITS / F5-TTS / Piper

Repo: https://github.com/zanezhao0708/voxagent

Works with anything that speaks MCP — tested with Claude Code, should work
with Cursor, OpenClaw, Codex.

What voice workflow would you actually use daily? The roadmap has streaming
STT and voice cloning next, but I'd rather build what people ask for.

---

## 3. V2EX / 即刻 / 少数派

**标题：** 给 Claude Code 装上耳朵和嘴巴——VoxAgent 开源了

**正文：**

写了个小工具 VoxAgent（MIT 协议）：让 Claude Code、Cursor 这类编程智能体
能听会说。

核心玩法三种：

1. MCP 三个工具：listen（听你说）、speak（它开口汇报）、ask_user（它提问你口头答）
2. Push-to-talk 守护进程：全局热键按住说话，松开转文字直通 claude -p，回复语音播报——人在厨房也能指挥它干活
3. Agent Skill：教会智能体"什么时候该说话"——回复短、长任务先预告、跟随你的语言

技术取向：识别端 faster-whisper 完全离线，合成端默认零配置，也可接本地
CosyVoice 服务用高质量中文音色。无 API Key、无云端依赖。

仓库：https://github.com/zanezhao0708/voxagent
演示：[GIF]

欢迎拍砖，下一步做流式识别还是音色克隆，听你们的。
