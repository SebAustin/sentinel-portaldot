# LangGraph Sentinel workflow — intent parse → validate → risk → multisig propose

from __future__ import annotations

import json
import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend.chain.portaldot import get_chain
from backend.config import settings
from backend.models.intent import ParsedIntent, PaymentIntent, RiskFlag
from backend.store.proposals import get_proposal, new_proposal_id, save_proposal, update_proposal
from backend.models.intent import MultisigProposal, ProposalStatus


class SentinelState(TypedDict, total=False):
    message: str
    parsed: ParsedIntent | None
    risk_flags: list[RiskFlag]
    rejected: bool
    reject_reason: str
    proposal_id: str
    proposal: MultisigProposal | None
    error: str


SS58_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{47,48}\b")
AMOUNT_RE = re.compile(r"(?P<amount>\d+(?:\.\d+)?)\s*POT\b", re.IGNORECASE)


def _parse_with_regex(message: str) -> ParsedIntent | None:
    addr_match = SS58_RE.search(message)
    amount_match = AMOUNT_RE.search(message)
    if not addr_match or not amount_match:
        return None
    memo = message.strip()
    return ParsedIntent(
        intent=PaymentIntent(
            recipient=addr_match.group(0),
            amount_pot=float(amount_match.group("amount")),
            memo=memo,
            category="treasury",
        ),
        confidence=0.85,
        raw_message=message,
    )


def _parse_with_llm(message: str) -> ParsedIntent | None:
    if not settings.anthropic_api_key:
        return None
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key=settings.anthropic_api_key)
        system = (
            "Extract treasury payment intent as JSON with keys: recipient (SS58 address), "
            "amount_pot (number), memo (string), category (string). Reply JSON only."
        )
        response = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=message)]
        )
        data = json.loads(response.content)
        return ParsedIntent(
            intent=PaymentIntent(**data),
            confidence=0.95,
            raw_message=message,
        )
    except Exception:
        return None


def parse_intent(state: SentinelState) -> SentinelState:
    message = state["message"]
    parsed = _parse_with_llm(message) or _parse_with_regex(message)
    if parsed is None:
        return {
            **state,
            "rejected": True,
            "reject_reason": "Could not parse recipient address and POT amount from message.",
        }
    return {**state, "parsed": parsed, "risk_flags": []}


def validate_intent(state: SentinelState) -> SentinelState:
    if state.get("rejected"):
        return state
    parsed = state.get("parsed")
    if parsed is None:
        return {**state, "rejected": True, "reject_reason": "Missing parsed intent."}

    intent = parsed.intent
    if intent.amount_pot <= 0:
        return {**state, "rejected": True, "reject_reason": "Amount must be positive."}

    chain = get_chain()
    try:
        chain.query_balance(intent.recipient)
    except Exception as exc:
        return {
            **state,
            "rejected": True,
            "reject_reason": f"Invalid recipient or chain unavailable: {exc}",
        }
    return state


def risk_gate(state: SentinelState) -> SentinelState:
    if state.get("rejected"):
        return state
    parsed = state["parsed"]
    flags: list[RiskFlag] = list(state.get("risk_flags") or [])
    amount = parsed.intent.amount_pot

    if amount > settings.max_transfer_pot:
        return {
            **state,
            "rejected": True,
            "reject_reason": f"Transfer {amount} POT exceeds demo limit of {settings.max_transfer_pot} POT.",
            "risk_flags": flags
            + [
                RiskFlag(
                    code="MAX_AMOUNT",
                    message=f"Blocked: max {settings.max_transfer_pot} POT per transfer",
                    severity="error",
                )
            ],
        }

    if amount >= 50:
        flags.append(
            RiskFlag(
                code="HIGH_VALUE",
                message="High-value transfer flagged for human review",
                severity="warning",
            )
        )

    return {**state, "risk_flags": flags}


def build_multisig_call(state: SentinelState) -> SentinelState:
    if state.get("rejected"):
        return state
    chain = get_chain()
    parsed = state["parsed"]
    intent = parsed.intent

    try:
        result = chain.propose_multisig_transfer(intent.recipient, intent.amount_pot)
    except Exception as exc:
        return {**state, "rejected": True, "reject_reason": str(exc), "error": str(exc)}

    proposal_id = new_proposal_id()
    proposal = MultisigProposal(
        id=proposal_id,
        intent=intent,
        call_hash=result.call_hash,
        multisig_address=result.multisig_address,
        threshold=result.threshold,
        signatories=result.signatories,
        approvals=1,
        status=ProposalStatus.PROPOSED,
        propose_tx_hash=result.propose_tx_hash,
        block_hash=result.block_hash,
        risk_flags=state.get("risk_flags") or [],
        timepoint=result.timepoint,
        max_weight=result.max_weight,
    )
    save_proposal(proposal)
    return {**state, "proposal_id": proposal_id, "proposal": proposal}


def finalize(state: SentinelState) -> SentinelState:
    return state


def _route_after_parse(state: SentinelState) -> str:
    return "validate" if not state.get("rejected") else END


def _route_after_validate(state: SentinelState) -> str:
    return "risk_gate" if not state.get("rejected") else END


def _route_after_risk(state: SentinelState) -> str:
    return "build_multisig" if not state.get("rejected") else END


def build_graph():
    graph = StateGraph(SentinelState)
    graph.add_node("parse_intent", parse_intent)
    graph.add_node("validate", validate_intent)
    graph.add_node("risk_gate", risk_gate)
    graph.add_node("build_multisig", build_multisig_call)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("parse_intent")
    graph.add_conditional_edges("parse_intent", _route_after_parse, {"validate": "validate", END: END})
    graph.add_conditional_edges("validate", _route_after_validate, {"risk_gate": "risk_gate", END: END})
    graph.add_conditional_edges("risk_gate", _route_after_risk, {"build_multisig": "build_multisig", END: END})
    graph.add_edge("build_multisig", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


sentinel_graph = build_graph()


def run_propose(message: str) -> SentinelState:
    return sentinel_graph.invoke({"message": message})


def run_finalize_proposal(proposal_id: str, approver_seed: str = "//Bob") -> MultisigProposal | None:
    proposal = get_proposal(proposal_id)
    if proposal is None:
        return None
    if proposal.status in (ProposalStatus.EXECUTED, ProposalStatus.APPROVED):
        return proposal

    chain = get_chain()
    try:
        result = chain.finalize_multisig_transfer(
            proposal.intent.recipient,
            proposal.intent.amount_pot,
            approver_seed=approver_seed,
            call_hash=proposal.call_hash,
            timepoint=proposal.timepoint,
        )
    except Exception as exc:
        update_proposal(proposal_id, status=ProposalStatus.FAILED)
        raise exc

    return update_proposal(
        proposal_id,
        status=ProposalStatus.EXECUTED,
        approvals=proposal.threshold,
        execute_tx_hash=result["execute_tx_hash"],
        block_hash=result["block_hash"],
    )
