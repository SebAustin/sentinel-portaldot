// Sentinel API client — talks to FastAPI LangGraph backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Proposal = {
  id: string;
  intent: {
    recipient: string;
    amount_pot: number;
    memo: string;
    category: string;
  };
  call_hash: string;
  multisig_address: string;
  threshold: number;
  signatories: string[];
  approvals: number;
  status: string;
  propose_tx_hash?: string;
  execute_tx_hash?: string;
  block_hash?: string;
  risk_flags: { code: string; message: string; severity: string }[];
  timepoint?: { height: number; index: number };
};

export async function proposePayment(message: string) {
  const res = await fetch(`${API_URL}/agent/propose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.reason || data.detail || "Proposal failed");
  return data as { proposal: Proposal; parsed: unknown };
}

export async function listProposals(): Promise<Proposal[]> {
  const res = await fetch(`${API_URL}/proposals`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load proposals");
  return res.json();
}

export async function finalizeProposal(id: string) {
  const res = await fetch(`${API_URL}/proposals/${id}/finalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approver_seed: "//Bob" }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Finalize failed");
  return data as Proposal;
}

export async function chainHealth() {
  const res = await fetch(`${API_URL}/chain/health`, { cache: "no-store" });
  return res.json();
}

export async function chainMultisig() {
  const res = await fetch(`${API_URL}/chain/multisig`, { cache: "no-store" });
  return res.json();
}
