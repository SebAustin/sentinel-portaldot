# In-memory proposal store for demo — tracks multisig approval state

from __future__ import annotations

import uuid
from threading import Lock

from backend.models.intent import MultisigProposal, ProposalStatus

_store: dict[str, MultisigProposal] = {}
_lock = Lock()


def save_proposal(proposal: MultisigProposal) -> MultisigProposal:
    with _lock:
        _store[proposal.id] = proposal
    return proposal


def get_proposal(proposal_id: str) -> MultisigProposal | None:
    with _lock:
        return _store.get(proposal_id)


def list_proposals() -> list[MultisigProposal]:
    with _lock:
        return list(_store.values())


def update_proposal(proposal_id: str, **updates) -> MultisigProposal | None:
    with _lock:
        existing = _store.get(proposal_id)
        if existing is None:
            return None
        updated = existing.model_copy(update=updates)
        _store[proposal_id] = updated
        return updated


def new_proposal_id() -> str:
    return str(uuid.uuid4())[:8]
