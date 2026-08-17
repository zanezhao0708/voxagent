---
name: voice-control
description: Hands-free voice interaction for coding agents. Use when the user wants to talk instead of type — dictate instructions by microphone, get spoken progress updates, or ask spoken questions mid-task. Covers phrases like "语音模式", "listen to me", "voice mode", "read that aloud", "ask me by voice".
---

# Voice Control

You have voice tools from the `voxagent` MCP server. Use them to interact by
voice — never guess what the user said, always call a tool.

## When to use

- The user says "voice mode / 语音模式 / listen up" → switch to voice: all
  further questions and confirmations go through `ask_user`, summaries via
  `speak`.
- The user asks you to "read this aloud / 念一下" → `speak` a condensed
  version (max 2 sentences).
- The user says "take dictation / 我说你们记" → call `listen` and treat the
  transcript as their message.

## Rules

1. **Spoken replies must be short.** Max 2 sentences per `speak` call.
   Details stay in the chat; voice carries the headline.
2. **Never invent audio input.** If `listen` returns "[nothing heard]", say so
   and retry once, then fall back to text.
3. **Language mirroring.** Reply by voice in the language the user spoke.
   Transcripts may be mixed-language; follow the dominant one.
4. **Announce long tasks.** Before a step that takes >30s (builds, big
   refactors, test suites), `speak` a one-line heads-up like "Tests are
   running, about a minute."
5. **Errors are spoken too.** If something fails while in voice mode, `speak`
   a one-liner plus the fix you are attempting.
6. **Degrade gracefully when voice fails.** If `speak` errors or returns `0`,
   do not retry in a loop — deliver the same message as text and note that
   audio is unavailable. Voice is an enhancement, never a blocker.

## Push-to-talk context

The user may drive you with the global push-to-talk hotkey instead of typing.
Transcripts then arrive as plain messages with no "voice mode" preamble. Treat
a short, imperative spoken-style message (e.g. "run the tests") as a voice
instruction and reply with a brief `speak` confirmation plus the normal text
detail.

## When voice fails

- `listen` → "[nothing heard]": retry once, then continue in text.
- `speak` errors: fall back to text; suggest `voxagent doctor` to the user.
- Repeated STT/TTS failures: tell the user to run `voxagent doctor` and check
  mic permission / `pip install 'voxagent[local]'`.

## Example flow

```
User (text): 语音模式
You:  speak("Voice mode on. What should we build?")
      ask_user("Ready when you are — what's the task?")   # -> transcript
      ... do the work, speak() short updates between steps ...
      speak("Done. All tests pass.")
```
