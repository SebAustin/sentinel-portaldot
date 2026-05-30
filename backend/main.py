# FastAPI entry — exposes Sentinel agent and Portaldot multisig proposal API

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.chain.portaldot import get_chain
from backend.config import settings
from backend.graph.sentinel_graph import run_finalize_proposal, run_propose
from backend.store.proposals import get_proposal, list_proposals

app = FastAPI(
    title="Sentinel Treasury Copilot",
    description="LangGraph agent proposing Portaldot multisig treasury transfers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProposeRequest(BaseModel):
    message: str = Field(min_length=3, examples=["Pay 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY 1 POT for audit"])


class FinalizeRequest(BaseModel):
    approver_seed: str = Field(default="//Bob", description="Dev-only: Bob approves demo multisig")


@app.get("/health")
def health():
    return {"status": "ok", "service": "sentinel"}


@app.get("/chain/health")
def chain_health():
    return get_chain().health()


@app.get("/chain/multisig")
def chain_multisig():
    chain = get_chain()
    multisig = chain.get_demo_multisig()
    balance = chain.query_balance(multisig.ss58_address)
    return {
        "multisig_address": multisig.ss58_address,
        "threshold": multisig.threshold,
        "signatories": multisig.signatories,
        "balance": balance,
    }


@app.post("/agent/propose")
def agent_propose(body: ProposeRequest):
    result = run_propose(body.message)
    if result.get("rejected"):
        raise HTTPException(
            status_code=422,
            detail={
                "reason": result.get("reject_reason", "Proposal rejected"),
                "risk_flags": [f.model_dump() for f in result.get("risk_flags") or []],
            },
        )
    proposal = result.get("proposal")
    if proposal is None:
        raise HTTPException(status_code=500, detail="Proposal not created")
    return {
        "proposal": proposal.model_dump(),
        "parsed": result.get("parsed").model_dump() if result.get("parsed") else None,
    }


@app.get("/proposals")
def proposals_list():
    return [p.model_dump() for p in list_proposals()]


@app.get("/proposals/{proposal_id}")
def proposal_get(proposal_id: str):
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    chain = get_chain()
    pending = chain.get_multisig_pending(proposal.call_hash)
    data = proposal.model_dump()
    data["on_chain_pending"] = pending
    return data


@app.post("/proposals/{proposal_id}/finalize")
def proposal_finalize(proposal_id: str, body: FinalizeRequest | None = None):
    seed = body.approver_seed if body else "//Bob"
    try:
        updated = run_finalize_proposal(proposal_id, approver_seed=seed)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return updated.model_dump()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
