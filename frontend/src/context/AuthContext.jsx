// src/context/AuthContext.jsx
import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.currentUser().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  async function registerParent(payload) {
    const u = await api.registerParent(payload);
    setUser(u);
    return u;
  }

  async function registerChild(payload) {
    const u = await api.registerChild(payload);
    setUser(u);
    return u;
  }

  async function login(payload) {
    const u = await api.login(payload);
    setUser(u);
    return u;
  }

  async function logout() {
    await api.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, registerParent, registerChild, login, logout, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
