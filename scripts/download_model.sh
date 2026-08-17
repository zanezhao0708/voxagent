#!/usr/bin/env bash
# Download a faster-whisper model directly from the hf-mirror.com CDN,
# bypassing the huggingface_hub SDK (which often fails behind the GFW or
# on flaky networks). Supports: tiny | base | small
#
# Usage:
#   bash scripts/download_model.sh            # tiny -> ~/.voxagent/models/tiny
#   bash scripts/download_model.sh base       # base -> ~/.voxagent/models/base
#   bash scripts/download_model.sh small /tmp/ws
#
# Then point VoxAgent at it:
#   export WHISPER_MODEL="$HOME/.voxagent/models/tiny"
set -euo pipefail

SIZE="${1:-tiny}"
DIR="${2:-$HOME/.voxagent/models/$SIZE}"

case "$SIZE" in
  tiny|base|small) ;;
  *) echo "error: size must be tiny | base | small (got '$SIZE')" >&2; exit 1 ;;
esac

BASE="https://hf-mirror.com/Systran/faster-whisper-$SIZE/resolve/main"
mkdir -p "$DIR"

for f in config.json model.bin tokenizer.json vocabulary.txt; do
  echo "→ downloading $SIZE/$f"
  curl -L --fail --retry 3 --retry-delay 2 -o "$DIR/$f" "$BASE/$f"
done

echo
echo "Done. Model cached at: $DIR"
echo "Enable it with:"
echo "  export WHISPER_MODEL=\"$DIR\""
