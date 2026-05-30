# Semantic payment intent schema — parsed natural-language treasury requests

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    PENDING = "pending"
    PROPOSED = "proposed"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"


class PaymentIntent(BaseModel):
    recipient: str = Field(description="SS58 recipient address")
    amount_pot: float = Field(gt=0, description="Amount in POT (human units)")
    memo: str = Field(default="", description="Payment reason or memo")
    category: str = Field(default="general", description="Expense category")


class RiskFlag(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class ParsedIntent(BaseModel):
    intent: PaymentIntent
    confidence: float = 1.0
    raw_message: str


class MultisigProposal(BaseModel):
    id: str
    intent: PaymentIntent
    call_hash: str
    multisig_address: str
    threshold: int
    signatories: list[str]
    approvals: int = 0
    status: ProposalStatus = ProposalStatus.PROPOSED
    propose_tx_hash: str | None = None
    execute_tx_hash: str | None = None
    block_hash: str | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    timepoint: dict | None = None
    max_weight: dict | None = None
