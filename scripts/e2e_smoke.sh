#!/usr/bin/env bash
# Run full Sentinel E2E smoke test against local Portaldot node + API
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
export PYTHONPATH=.

echo "=== Chain health ==="
curl -sf http://localhost:8000/chain/health | python3 -m json.tool

echo "=== Propose ==="
RESP=$(curl -sf -X POST http://localhost:8000/agent/propose \
  -H 'Content-Type: application/json' \
  -d '{"message":"Pay 5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y 1 POT for audit report"}')
echo "$RESP" | python3 -m json.tool | head -20
PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['proposal']['id'])")

echo "=== Finalize $PID ==="
curl -sf -X POST "http://localhost:8000/proposals/$PID/finalize" \
  -H 'Content-Type: application/json' \
  -d '{"approver_seed":"//Bob"}' | python3 -m json.tool | head -15

echo "E2E smoke test PASSED"
