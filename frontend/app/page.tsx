"use client";

// Chat + propose screen — natural language to Portaldot multisig proposal

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { chainHealth, proposePayment, type Proposal } from "@/lib/api";

const DEMO_MESSAGE =
  "Pay 5FLSigC9HGRKVhB9FiEo4Y3koPsNmBmLJbpXg2mp1hXcS59Y 1 POT for audit report";

export default function HomePage() {
  const [message, setMessage] = useState(DEMO_MESSAGE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [chain, setChain] = useState<{ connected?: boolean; block_number?: number } | null>(null);

  async function handlePropose() {
    setLoading(true);
    setError(null);
    try {
      const health = await chainHealth();
      setChain(health);
      if (!health.connected) {
        throw new Error("Portaldot node not connected. Start portaldot_dev --dev --tmp");
      }
      const result = await proposePayment(message);
      setProposal(result.proposal);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Treasury intent</CardTitle>
          <CardDescription>
            Describe a payment in plain language. Sentinel parses, validates, and proposes on-chain
            via Portaldot multisig.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea value={message} onChange={(e) => setMessage(e.target.value)} />
          <div className="flex flex-wrap gap-3">
            <Button onClick={handlePropose} disabled={loading}>
              {loading ? "Proposing…" : "Propose on-chain"}
            </Button>
            <Button variant="outline" asChild>
              <Link href="/approvals">View approvals →</Link>
            </Button>
          </div>
          {error && (
            <p className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200">
              {error}
            </p>
          )}
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Chain status</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {chain ? (
              <ul className="space-y-1">
                <li>Connected: {chain.connected ? "yes" : "no"}</li>
                <li>Block: {chain.block_number ?? "—"}</li>
              </ul>
            ) : (
              <p>Submit a proposal to check chain health.</p>
            )}
          </CardContent>
        </Card>

        {proposal && (
          <Card className="border-primary/40">
            <CardHeader>
              <CardTitle>Proposal {proposal.id}</CardTitle>
              <CardDescription>
                Status: {proposal.status} · {proposal.approvals}/{proposal.threshold} approvals
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 font-mono text-xs">
              <p>Recipient: {proposal.intent.recipient}</p>
              <p>Amount: {proposal.intent.amount_pot} POT</p>
              <p>Multisig: {proposal.multisig_address}</p>
              <p>Call hash: {proposal.call_hash}</p>
              <p>Propose tx: {proposal.propose_tx_hash}</p>
              {proposal.risk_flags.map((f) => (
                <p key={f.code} className="text-amber-300">
                  {f.message}
                </p>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
