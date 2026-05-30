# DoraHacks BUIDL Description — Sentinel Treasury Copilot

## What is the problem?

DAO and team treasuries increasingly use AI assistants to draft payments, vendor invoices, and grant disbursements. But giving an LLM direct signing access creates a single point of failure: one prompt injection or model mistake can drain funds. Teams need AI speed with **on-chain, cryptographically enforced** approval thresholds — not trust in a web app toggle.

## Why does it matter?

Treasury operations fail when policy lives off-chain. Multisig wallets solve this, but composing Substrate extrinsics, ordering signatories, and tracking timepoints is error-prone for non-protocol engineers. Sentinel bridges natural-language intent to Portaldot's native **multisig pallet**, so security guarantees come from the chain runtime, not the agent.

## Who is it for?

- DAO treasury stewards who want AI-assisted drafting with human/co-signer approval
- Portaldot ecosystem teams demonstrating LAO NPoS Layer-0 + enterprise account patterns
- Hackathon judges evaluating **load-bearing** Portaldot integration (not bolt-on Web3)

## How does it work?

1. **Intent**: User types a payment request (recipient SS58, POT amount, memo).
2. **Agent (LangGraph)**: Parses intent (regex + optional Claude), validates address/balance, applies demo risk limits (max 100 POT).
3. **Propose on-chain**: Backend connects via `substrate-interface` to a Portaldot dev node and submits **`Multisig.asMulti`** signed by Alice — first approval of a 2-of-3 multisig.
4. **Human approve**: Second signer (Bob in demo, Polkadot.js extension in production path) finalizes via another **`asMulti`** with the stored timepoint — Portaldot executes `Balances.transfer_keep_alive`.
5. **Audit trail**: UI shows call hash, propose tx, execute tx, and block hash.

Sentinel never holds unilateral signing authority. The multisig pallet enforces threshold logic; the agent only initiates proposals.

### Portaldot primitives

- **multisig pallet**: `asMulti` propose + finalize (core demo)
- **balances pallet**: POT transfers from derived multisig account
- **LAO NPoS runtime**: Portaldot Layer-0 dev node, POT token (14 decimals)

### Integration snippet

```python
receipt = submit_as_multi(
    substrate,
    payment_call,
    keypair_alice,
    multisig_account,
    maybe_timepoint=None,
)
# Second signer passes timepoint from Multisig storage → transfer executes
```

### Stack

LangGraph · FastAPI · Next.js · substrate-interface · Polkadot.js extension

### Live demo

Run locally per README (≤5 commands). Deploy: Vercel (frontend) + Render (backend) — add URLs before submission.

### What's next

ink! escrow modules, mainnet RPC, org-specific policy packs, full browser-side `approveAsMulti`.
