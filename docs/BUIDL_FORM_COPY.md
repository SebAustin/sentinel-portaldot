# DoraHacks BUIDL Form — Copy-Paste Guide

Use this when submitting on [Portaldot Online S1](https://dorahacks.io/hackathon/portaldot-online-s1/buidl).

---

## Page 1 — Project basics

### BUIDL (project) name *

```
Sentinel Treasury Copilot
```

**Alt short name:** `Sentinel`

---

### BUIDL logo *

Upload: [`assets/sentinel-buidl-logo.png`](../assets/sentinel-buidl-logo.png)  
(480×480 recommended, PNG/JPEG, under 2 MB)

---

### Vision * (max 256 characters)

```
AI can draft treasury payments, but should not sign alone. Sentinel routes intents through Portaldot 2-of-3 multisig—POT moves only after on-chain co-signer approval.
```

(163 characters)

**Alternate:**

```
Teams want AI to draft payments, not hold hot keys. Sentinel turns natural-language requests into Portaldot multisig proposals; funds move only after threshold approval on-chain.
```

(175 characters)

---

### Category *

Select: **Crypto / Web3**

(Optional second if allowed: **AI / Robotics** — project uses LangGraph)

---

### Is this BUIDL an AI Agent? *

Toggle: **Yes**

---

## Page 2 — Links

### GitHub/Gitlab/Bitbucket *

After you push the repo:

```
https://github.com/SebAustin/sentinel-portaldot
```

**Push checklist:**

```bash
cd "Portaldot Online Mini Hackathon S1"
git add -A && git commit -m "feat: Sentinel Portaldot multisig treasury copilot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sentinel-portaldot.git
git push -u origin main
```

---

### Project website (optional)

Use one of:

- Local demo: `http://localhost:3000` (not ideal for judges)
- Vercel after deploy: `https://sentinel-portaldot.vercel.app`
- GitHub README: `https://github.com/YOUR_USERNAME/sentinel-portaldot#readme`

Leave blank until deployed, or use GitHub README link.

---

### Demo video *

Record 90–180s, upload to YouTube (unlisted is fine), then paste:

```
https://www.youtube.com/watch?v=YOUR_VIDEO_ID
```

**Suggested script:**

| Time | Say / Show |
|------|------------|
| 0:00–0:10 | "AI can draft payments—but shouldn't sign alone." |
| 0:10–0:30 | Treasury risk: single hot key, need on-chain multisig |
| 0:30–1:00 | Intro Sentinel + Portaldot multisig pallet |
| 1:00–2:00 | Live: chat propose → approvals → tx hash on screen |
| 2:00–2:30 | "Built with Portaldot" — name multisig + LAO NPoS chain |

---

### Social links (at least one) *

Pick 1–3 you actually use, e.g.:

```
https://x.com/YOUR_HANDLE
```

```
https://github.com/YOUR_USERNAME
```

```
https://www.linkedin.com/in/YOUR_PROFILE
```

---

## Long description (if form has a separate Description / Details field)

Paste from [`BUIDL_DESCRIPTION.md`](BUIDL_DESCRIPTION.md) or this block (≥250 words):

```
What is the problem?
DAO and team treasuries increasingly use AI assistants to draft payments, vendor invoices, and grant disbursements. But giving an LLM direct signing access creates a single point of failure: one prompt injection or model mistake can drain funds. Teams need AI speed with on-chain, cryptographically enforced approval thresholds—not trust in a web app toggle.

Why does it matter?
Treasury operations fail when policy lives off-chain. Multisig wallets solve this, but composing Substrate extrinsics, ordering signatories, and tracking timepoints is error-prone. Sentinel bridges natural-language intent to Portaldot's native multisig pallet, so security guarantees come from the chain runtime, not the agent.

Who is it for?
DAO treasury stewards, Portaldot ecosystem builders, and teams who want AI-assisted ops with human-in-the-loop on-chain approval.

How does it work?
1. User types a payment intent (recipient, POT amount, memo).
2. LangGraph agent parses, validates SS58 address, checks balance, applies risk limits.
3. Backend submits Multisig.asMulti to Portaldot (first signature, 2-of-3).
4. Second signer approves via Multisig.asMulti with timepoint—Balances.transfer_keep_alive executes.
5. UI shows call hash, propose tx, execute tx, block hash.

Built with Portaldot: multisig pallet (load-bearing), balances pallet, LAO NPoS dev runtime, POT token. Stack: LangGraph, FastAPI, Next.js, substrate-interface.
```

---

## Built with Portaldot section (for judges / extra fields)

**Paragraph:**

Sentinel uses Portaldot's **multisig pallet** as the load-bearing security layer. The LangGraph agent composes `Balances.transfer_keep_alive` calls and submits them via `Multisig.asMulti`—never with unilateral signing authority. A second co-signer must finalize on-chain before POT moves. We verified integration with `scripts/proof_of_life_multisig.py` and live extrinsics on the Portaldot dev node (chain portaldot/1002, POT, ss58 42, LAO NPoS).

**Code snippet (10–20 lines):** see README "Built with Portaldot" section.

**Screenshot:** capture Approvals page showing pending proposal + executed tx hash.

---

## Pre-submit checklist

- [ ] Logo uploaded
- [ ] GitHub public + commits in Apr 20–May 31 window
- [ ] Demo video on YouTube
- [ ] At least one social link
- [ ] AI Agent = Yes
- [ ] Category = Crypto / Web3
- [ ] No `.env` secrets in repo
