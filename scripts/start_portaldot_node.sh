#!/usr/bin/env bash
# Start Portaldot local dev node — requires portaldot_dev binary on PATH
set -euo pipefail

BINARY="${PORTALDOT_DEV_BINARY:-$(cd "$(dirname "$0")/.." && pwd)/bin/portaldot-testnet-macos/portaldot_dev}"
WS_PORT="${PORTALDOT_WS_PORT:-9944}"

if ! command -v "$BINARY" >/dev/null 2>&1; then
  echo "Error: $BINARY not found."
  echo "Download Portaldot dev node from portaldot.io / hackathon docs."
  echo "Then: export PORTALDOT_DEV_BINARY=/path/to/portaldot_dev"
  exit 1
fi

echo "Starting Portaldot dev node on ws://127.0.0.1:${WS_PORT} ..."
exec "$BINARY" --dev --tmp --ws-port "$WS_PORT"
