import { useEffect, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import AppShell from "../components/AppShell";
import { Card, Button, Eyebrow, Input } from "../components/ui";
import TransactionRow from "../components/TransactionRow";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { formatRupees } from "../lib/money";

export default function ParentDashboard() {
  const { user } = useAuth();
  const [family, setFamily] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [pairCode, setPairCode] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [decidingId, setDecidingId] = useState(null);
  const [savingChildId, setSavingChildId] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [fam, tx] = await Promise.all([api.getFamily(user.id), api.getTransactions(user)]);
    setFamily(fam);
    setTransactions(tx);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleGenerateCode() {
    setGenerating(true);
    const { code } = await api.generatePairCode(user.id);
    setPairCode(code);
    setGenerating(false);
  }

  async function handleDecide(txId, decision) {
    setDecidingId(txId);
    await api.decideTransaction({ txId, decision });
    await refresh();
    setDecidingId(null);
  }

  async function saveControls(child) {
    setSavingChildId(child.id);
    await api.updateChildControls({
      childId: child.id,
      balanceLimit: child.balance_limit || 0,
      walletBalance: child.wallet_balance || 0,
    });
    await refresh();
    setSavingChildId(null);
  }

  function updateChildDraft(childId, key, value) {
    setFamily((rows) => rows.map((c) => (c.id === childId ? { ...c, [key]: value } : c)));
  }

  const pending = transactions.filter((t) => t.status === "pending");
  const decided = transactions.filter((t) => t.status !== "pending");
  const approvedTotal = transactions
    .filter((t) => t.status === "approved")
    .reduce((sum, t) => sum + Number(t.amount || 0), 0);
  const childMap = Object.fromEntries(family.map((c) => [c.id, c.name]));

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <Eyebrow>Parent account</Eyebrow>
          <h1 className="font-display text-3xl text-ink mt-1">
            {pending.length > 0
              ? `${pending.length} request${pending.length > 1 ? "s" : ""} waiting for you`
              : "Nothing pending right now"}
          </h1>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Card className="p-6">
          <Eyebrow>Open requests</Eyebrow>
          <p className="font-display text-3xl text-ink mt-2">{pending.length}</p>
        </Card>
        <Card className="p-6">
          <Eyebrow>Approved spend</Eyebrow>
          <p className="font-display text-3xl text-ink mt-2">{formatRupees(approvedTotal)}</p>
        </Card>
        <Card className="p-6">
          <Eyebrow>Children</Eyebrow>
          <p className="font-display text-3xl text-ink mt-2">{family.length}</p>
        </Card>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Card className="p-6 md:col-span-1">
          <Eyebrow>Pairing</Eyebrow>
          <h2 className="font-display text-xl text-ink mt-1 mb-3">Add a child</h2>
          <p className="text-sm text-slate/65 mb-4 leading-relaxed">
            Make one code and share it with your child. It expires in 30 minutes.
          </p>
          <Button variant="brass" onClick={handleGenerateCode} disabled={generating} className="w-full">
            {generating ? "Making code..." : "Make pairing code"}
          </Button>
          <AnimatePresence>
            {pairCode && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 overflow-hidden"
              >
                <div className="relative bg-ink text-parchment rounded-lg px-4 py-4 text-center">
                  <span className="block text-[10px] uppercase tracking-[0.2em] text-brass/80 mb-1">
                    One-time code
                  </span>
                  <span className="font-mono text-2xl tracking-[0.15em]">{pairCode}</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>

        <Card className="p-6 md:col-span-2">
          <Eyebrow>Family wallet</Eyebrow>
          <h2 className="font-display text-xl text-ink mt-1 mb-4">
            {family.length === 0 ? "No one added yet" : "Balances and limits"}
          </h2>
          {family.length === 0 ? (
            <p className="text-sm text-slate/60">
              Make a code on the left, then ask your child to join with it.
            </p>
          ) : (
            <ul className="space-y-4">
              {family.map((c) => (
                <li key={c.id} className="grid sm:grid-cols-[1fr_120px_120px_auto] gap-3 items-end">
                  <div>
                    <p className="font-medium text-ink">{c.name}</p>
                    <p className="font-mono text-xs text-slate/40">@{c.username}</p>
                  </div>
                  <Input
                    label="Wallet"
                    type="number"
                    min="0"
                    step="0.01"
                    value={c.wallet_balance ?? 0}
                    onChange={(e) => updateChildDraft(c.id, "wallet_balance", e.target.value)}
                  />
                  <Input
                    label="Limit"
                    type="number"
                    min="0"
                    step="0.01"
                    value={c.balance_limit ?? 0}
                    onChange={(e) => updateChildDraft(c.id, "balance_limit", e.target.value)}
                  />
                  <Button
                    variant="ghost"
                    className="!px-3 !py-2"
                    disabled={savingChildId === c.id}
                    onClick={() => saveControls(c)}
                  >
                    Save
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="p-6">
        <Eyebrow>Pending requests</Eyebrow>
        <h2 className="font-display text-xl text-ink mt-1 mb-2">Waiting for your approval</h2>
        {loading ? (
          <SkeletonRows />
        ) : pending.length === 0 ? (
          <EmptyState text="No open requests right now. New ones will show up here when your child sends them." />
        ) : (
          <AnimatePresence>
            {pending.map((tx) => (
              <TransactionRow
                key={tx.id}
                tx={tx}
                childName={childMap[tx.childId]}
                showActions
                onDecide={handleDecide}
                deciding={decidingId === tx.id}
              />
            ))}
          </AnimatePresence>
        )}
      </Card>

      {decided.length > 0 && (
        <Card className="p-6 mt-6">
          <Eyebrow>History</Eyebrow>
          <h2 className="font-display text-xl text-ink mt-1 mb-2">Already handled</h2>
          {decided.map((tx) => (
            <TransactionRow key={tx.id} tx={tx} childName={childMap[tx.childId]} />
          ))}
        </Card>
      )}
    </AppShell>
  );
}

function EmptyState({ text }) {
  return (
    <div className="py-10 text-center">
      <p className="text-sm text-slate/55 max-w-sm mx-auto">{text}</p>
    </div>
  );
}

function SkeletonRows() {
  return (
    <div className="space-y-3 py-2">
      {[1, 2].map((i) => (
        <div key={i} className="h-14 rounded-md bg-ink/5 animate-pulse" />
      ))}
    </div>
  );
}
