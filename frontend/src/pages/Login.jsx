// src/pages/Login.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button, Input } from "../components/ui";
import { AuthFrame } from "./RegisterParent";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
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
      const user = await login(form);
      navigate(user.role === "parent" ? "/parent" : "/child");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFrame eyebrow="Welcome back" title="Sign in">
      <form onSubmit={onSubmit} className="space-y-4 mt-5">
        <Input label="Username" required value={form.username} onChange={update("username")} />
        <Input
          label="Password"
          type="password"
          required
          value={form.password}
          onChange={update("password")}
        />
        {error && <p className="text-sm text-rust">{error}</p>}
        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? "Checking…" : "Sign in"}
        </Button>
      </form>
      <p className="text-sm text-slate/60 mt-6 text-center">
        New here?{" "}
        <Link to="/register" className="font-semibold text-ink hover:text-brassdark">
          Register as a parent
        </Link>{" "}
        or{" "}
        <Link to="/register-child" className="font-semibold text-ink hover:text-brassdark">
          claim a pairing code
        </Link>
      </p>
    </AuthFrame>
  );
}
