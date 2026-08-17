# Examples

## `demo_cli.py` — standalone talk-loop

The fastest way to feel VoxAgent without wiring up an agent:

```bash
pip install 'voxagent[local]'
python examples/demo_cli.py
```

Press Enter, speak, pause — it transcribes with faster-whisper and reads the
result back with your TTS engine. No MCP client required.

## CosyVoice recipe — high-quality local Chinese voices

The default TTS (`edge-tts`) needs no setup but contacts Microsoft's service.
For fully offline, production-quality speech, run a local
[CosyVoice](https://github.com/FunAudioLLM/CosyVoice) API server and point
VoxAgent at it:

```bash
# 1. Start CosyVoice's web API (default port 9880) per its docs, e.g.:
#    python webui.py --port 9880

# 2. Point VoxAgent at it
export VOXAGENT_TTS_ENGINE=cosyvoice
export COSYVOICE_BASE_URL=http://127.0.0.1:9880

# 3. Run anything as usual
voxagent demo
```

That's the whole integration — the `cosyvoice` adapter is ~40 lines
(`voxagent/tts/cosyvoice_engine.py`), a good template if you want to add
GPT-SoVITS, F5-TTS or Piper.
