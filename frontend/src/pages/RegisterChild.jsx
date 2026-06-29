// src/pages/RegisterChild.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Input } from "../components/ui";
import { AuthFrame } from "./RegisterParent";
import { useAuth } from "../context/AuthContext";

export default function RegisterChild() {
  const { registerChild } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", username: "", password: "", pairCode: "" });
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
      await registerChild(form);
      navigate("/child");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFrame eyebrow="Step 2 of 2" title="Use your code">
      <p className="text-sm text-slate/70 mb-7">
        Ask your parent for the code shown on their dashboard. It looks like{" "}
        <span className="font-mono text-ink">ABC-123</span>.
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Pairing code"
          required
          value={form.pairCode}
          onChange={update("pairCode")}
          placeholder="ABC-123"
          className="font-mono uppercase tracking-widest text-center text-lg"
          maxLength={7}
        />
        <Input label="Your name" required value={form.name} onChange={update("name")} placeholder="Aanya" />
        <Input label="Choose a username" required value={form.username} onChange={update("username")} placeholder="aanya" />
        <Input
          label="Choose a password"
          type="password"
          required
          minLength={4}
          value={form.password}
          onChange={update("password")}
        />
        {error && <p className="text-sm text-rust">{error}</p>}
        <Button type="submit" variant="brass" className="w-full" disabled={loading}>
          {loading ? "Joining…" : "Join the account"}
        </Button>
      </form>
      <p className="text-sm text-slate/60 mt-6 text-center">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-ink hover:text-brassdark">
          Sign in
        </Link>
      </p>
    </AuthFrame>
  );
}
