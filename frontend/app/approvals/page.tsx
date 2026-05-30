"use client";

// Approvals queue — finalize Portaldot multisig proposals (Bob signer via backend)

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { connectExtension } from "@/lib/polkadot/multisig";
import { finalizeProposal, listProposals, type Proposal } from "@/lib/api";

export default function ApprovalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [wallet, setWallet] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setProposals(await listProposals());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  async function handleConnect() {
    setError(null);
    setInfo(null);
    const result = await connectExtension();
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setWallet(result.address);
    setInfo(`Extension connected (${result.accounts.length} account(s)). Approval still uses backend //Bob for demo.`);
  }

  async function handleApprove(proposal: Proposal) {
    setBusyId(proposal.id);
    setError(null);
    try {
      const updated = await finalizeProposal(proposal.id);
      setProposals((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setInfo(`Executed on Portaldot · tx ${updated.execute_tx_hash?.slice(0, 18)}…`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setBusyId(null);
    }
  }

  const pending = proposals.filter((p) => p.status === "proposed");
  const executed = proposals.filter((p) => p.status === "executed");

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Approval queue</h2>
          <p className="text-sm text-muted-foreground">
            Click <strong>Approve</strong> to finalize via Portaldot <code>Multisig.asMulti</code> (demo
            signer: //Bob on backend). Extension connect is optional.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleConnect}>
            {wallet ? `Extension: ${wallet.slice(0, 8)}…` : "Connect extension (optional)"}
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/">← New proposal</Link>
          </Button>
        </div>
      </div>

      {info && (
        <p className="rounded-md border border-primary/40 bg-primary/10 p-3 text-sm text-primary">
          {info}
        </p>
      )}

      {error && (
        <div className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200 space-y-2">
          <p>{error}</p>
          {error.includes("No accounts") && (
            <ol className="list-decimal list-inside text-xs opacity-90">
              <li>Install Polkadot.js extension if missing</li>
              <li>Open extension → + → Create account (any name)</li>
              <li>Or import dev seed: <code>//Bob</code></li>
              <li>You can still click Approve without the extension for this demo</li>
            </ol>
          )}
        </div>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Pending ({pending.length})</CardTitle>
            <CardDescription>1/{pending[0]?.threshold ?? 2} → needs second signature</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
            {!loading && pending.length === 0 && (
              <p className="text-sm text-muted-foreground">No pending proposals.</p>
            )}
            {pending.map((p) => (
              <div key={p.id} className="rounded-lg border border-border p-4 space-y-2">
                <p className="font-medium">
                  {p.intent.amount_pot} POT → {p.intent.recipient.slice(0, 12)}…
                </p>
                <p className="font-mono text-xs text-muted-foreground">call {p.call_hash.slice(0, 18)}…</p>
                <Button
                  size="sm"
                  onClick={() => handleApprove(p)}
                  disabled={busyId === p.id}
                >
                  {busyId === p.id ? "Signing…" : "Approve (Multisig.asMulti)"}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Activity</CardTitle>
            <CardDescription>Executed multisig transfers on Portaldot</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {executed.length === 0 && (
              <p className="text-sm text-muted-foreground">No executed transfers yet.</p>
            )}
            {executed.map((p) => (
              <div key={p.id} className="rounded-lg border border-primary/30 bg-primary/5 p-4 space-y-1">
                <p className="text-sm font-medium text-primary">Executed · {p.id}</p>
                <p className="font-mono text-xs break-all">tx {p.execute_tx_hash}</p>
                <p className="font-mono text-xs break-all">block {p.block_hash}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
