import { useEffect, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import AppShell from "../components/AppShell";
import { Card, Button, Input, Eyebrow } from "../components/ui";
import TransactionRow from "../components/TransactionRow";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { formatRupees } from "../lib/money";

export default function ChildDashboard() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ amount: "", merchant: "", note: "" });
  const [editingTx, setEditingTx] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const tx = await api.getTransactions(user);
    setTransactions(tx);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  function update(key) {
    return (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  function closeForm() {
    setShowForm(false);
    setEditingTx(null);
    setForm({ amount: "", merchant: "", note: "" });
    setError("");
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.amount || Number(form.amount) <= 0) {
      setError("Enter an amount greater than zero.");
      return;
    }
    setSubmitting(true);
    try {
      if (editingTx) {
        await api.updateTransaction({ txId: editingTx.id, ...form });
      } else {
        await api.createTransaction({ childId: user.id, ...form });
      }
      closeForm();
      await refresh();
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(tx) {
    setEditingTx(tx);
    setForm({ amount: String(tx.amount), merchant: tx.merchant, note: tx.note || "" });
    setShowForm(true);
  }

  async function handleCancel(txId) {
    await api.cancelTransaction(txId);
    await refresh();
  }

  async function handleReceipt(txId, file) {
    await api.uploadReceipt(txId, file);
    await refresh();
  }

  const pending = transactions.filter((t) => t.status === "pending");
  const decided = transactions.filter((t) => t.status !== "pending");

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <Eyebrow>Your account</Eyebrow>
          <h1 className="font-display text-3xl text-ink mt-1">
            {pending.length > 0 ? `${pending.length} waiting for approval` : "All clear"}
          </h1>
          <p className="text-sm text-slate/60 mt-2">
            Wallet {formatRupees(user.wallet_balance || 0)} - Limit {formatRupees(user.balance_limit || 0)}
          </p>
        </div>
        <Button variant="brass" onClick={() => (showForm ? closeForm() : setShowForm(true))}>
          {showForm ? "Close" : "Send a request"}
        </Button>
      </div>

      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mb-6"
          >
            <Card className="p-6">
              <Eyebrow>{editingTx ? "Pending edit" : "New request"}</Eyebrow>
              <h2 className="font-display text-xl text-ink mt-1 mb-4">
                {editingTx ? "Edit request before review" : "What do you need?"}
              </h2>
              <form onSubmit={onSubmit} className="grid sm:grid-cols-2 gap-4">
                <Input
                  label="Amount (INR)"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                  value={form.amount}
                  onChange={update("amount")}
                  placeholder="1200"
                />
                <Input
                  label="Merchant"
                  required
                  value={form.merchant}
                  onChange={update("merchant")}
                  placeholder="Stationery Shop"
                />
                <div className="sm:col-span-2">
                  <Input
                    label="Note (optional)"
                    value={form.note}
                    onChange={update("note")}
                    placeholder="School notebook and pens"
                  />
                </div>
                {error && <p className="text-sm text-rust sm:col-span-2">{error}</p>}
                <Button type="submit" variant="primary" disabled={submitting} className="sm:col-span-2">
                  {submitting ? "Saving..." : editingTx ? "Save changes" : "Send to parent"}
                </Button>
              </form>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <Card className="p-6">
        <Eyebrow>Pending</Eyebrow>
        <h2 className="font-display text-xl text-ink mt-1 mb-2">Waiting for approval</h2>
        {loading ? (
          <SkeletonRows />
        ) : pending.length === 0 ? (
          <EmptyState text="Nothing pending. Send a request and it will show up here." />
        ) : (
          <AnimatePresence>
            {pending.map((tx) => (
              <TransactionRow
                key={tx.id}
                tx={tx}
                canEdit
                onEdit={startEdit}
                onCancel={handleCancel}
                onUploadReceipt={handleReceipt}
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
            <TransactionRow key={tx.id} tx={tx} />
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
