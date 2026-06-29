// src/pages/RegisterParent.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Mark from "../components/Mark";
import { Button, Input, Eyebrow } from "../components/ui";
import { useAuth } from "../context/AuthContext";

export default function RegisterParent() {
  const { registerParent } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(key) {
    return (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await registerParent(form);
      navigate("/parent");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFrame eyebrow="Step 1 of 2" title="Start the family account">
      <p className="text-sm text-slate/70 mb-7">
        You register first as the parent. After that, you can make a code for your
        child to join.
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <Input label="Your name" required value={form.name} onChange={update("name")} placeholder="Aarav Sharma" />
        <Input label="Username" required value={form.username} onChange={update("username")} placeholder="aarav" />
        <Input
          label="Password"
          type="password"
          required
          minLength={4}
          value={form.password}
          onChange={update("password")}
          placeholder="••••••••"
        />
        {error && <p className="text-sm text-rust">{error}</p>}
        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? "Starting account…" : "Create parent account"}
        </Button>
      </form>
      <p className="text-sm text-slate/60 mt-6 text-center">
        Already registered?{" "}
        <Link to="/login" className="font-semibold text-ink hover:text-brassdark">
          Sign in
        </Link>
      </p>
    </AuthFrame>
  );
}

export function AuthFrame({ eyebrow, title, children }) {
  return (
    <div className="min-h-screen bg-parchment grain-overlay flex items-center justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <Link to="/" className="flex items-center gap-2 text-ink mb-8 justify-center">
          <Mark size={24} />
          <span className="font-display text-lg">Family Pocket</span>
        </Link>
        <div className="bg-white border border-ink/10 rounded-2xl shadow-card p-8">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h1 className="font-display text-3xl text-ink mt-2 mb-1">{title}</h1>
          {children}
        </div>
      </motion.div>
    </div>
  );
}
