# Architecture — Sentinel Treasury Copilot

## Components

- **frontend/** — Next.js chat + approval queue + activity feed
- **backend/main.py** — FastAPI routes
- **backend/graph/sentinel_graph.py** — LangGraph: parse → validate → risk → propose
- **backend/chain/portaldot.py** — SubstrateInterface wrapper
- **backend/chain/multisig_helpers.py** — Manual `Multisig.asMulti` (substrate-interface workaround)
- **scripts/proof_of_life_multisig.py** — SDK smoke test

## Demo flow

1. User enters: `Pay <SS58> 1 POT for audit`
2. LangGraph parses intent, checks max transfer, queries recipient balance
3. Alice (`//Alice`) submits first `asMulti` — stores pending multisig
4. Bob (`//Bob`) submits second `asMulti` with timepoint — executes transfer
5. UI shows propose + execute extrinsic hashes

## Multisig config (dev)

| Field | Value |
|-------|-------|
| Threshold | 2 |
| Signatories | //Alice, //Bob, //Charlie |
| Multisig address | Derived on-chain (see `/chain/multisig`) |

## Chain connection

| Setting | Default |
|---------|---------|
| WS | `ws://127.0.0.1:9944` |
| SS58 | 42 |
| Type registry | `polkadot` preset |
| POT decimals | 14 |

Download node: [Portaldot chain info](https://portaldot-dev.readthedocs.io/en/latest/chain-info.html) or `bash scripts/download_portaldot_node.sh`
