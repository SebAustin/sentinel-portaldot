#!/usr/bin/env bash
# Download Portaldot macOS dev node from official docs
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$ROOT/bin"
URL="https://github.com/portaldotVolunteer/Portaldot-node/raw/main/portaldot-testnet-macos.tar.gz"

mkdir -p "$BIN_DIR"
echo "Downloading Portaldot dev node..."
curl -L -o "$BIN_DIR/portaldot-testnet-macos.tar.gz" "$URL"
tar -xzf "$BIN_DIR/portaldot-testnet-macos.tar.gz" -C "$BIN_DIR"
chmod +x "$BIN_DIR/portaldot-testnet-macos/portaldot_dev"
echo "Ready: $BIN_DIR/portaldot-testnet-macos/portaldot_dev"
