// src/lib/api.js
//
// REAL BACKEND CLIENT -------------------------------------------------------
// Talks to the Flask backend. Same function names/shapes as the old
// localStorage mock (api.mock.js.bak) on purpose — every page that calls
// `api.whatever(...)` via AuthContext needed zero changes.
//
// Auth model: httpOnly session cookie (set by the backend on login/register)
// + a separate, readable `gl_csrf` cookie that must be echoed back as the
// `X-CSRF-Token` header on state-changing requests (POST/PUT/DELETE).
// `credentials: "include"` is required on every call so the cookies are
// actually sent/received.
// ---------------------------------------------------------------------------

const BASE_URL = import.meta.env.VITE_API_URL || ""; // "" -> same-origin via Vite proxy

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (method !== "GET") {
    const csrf = getCookie("gl_csrf");
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }

  const res = await fetch(`${BASE_URL}/api${path}`, {
    method,
    headers,
    credentials: "include",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Backend always returns JSON, even on errors -> { error } or { data }.
  const payload = await res.json().catch(() => null);

  if (!res.ok) {
    throw new Error(payload?.error || `Request failed (${res.status}).`);
  }
  return payload?.data;
}

async function requestForm(path, formData, { method = "POST" } = {}) {
  const headers = {};
  const csrf = getCookie("gl_csrf");
  if (csrf) headers["X-CSRF-Token"] = csrf;

  const res = await fetch(`${BASE_URL}/api${path}`, {
    method,
    headers,
    credentials: "include",
    body: formData,
  });

  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(payload?.error || `Request failed (${res.status}).`);
  }
  return payload?.data;
}

export const api = {
  async registerParent({ name, username, password }) {
    return request("/auth/register-parent", { method: "POST", body: { name, username, password } });
  },

  async login({ username, password }) {
    return request("/auth/login", { method: "POST", body: { username, password } });
  },

  async logout() {
    await request("/auth/logout", { method: "POST" });
  },

  async currentUser() {
    try {
      return await request("/auth/me");
    } catch {
      return null; // not logged in -> AuthContext treats this as "no user"
    }
  },

  async generatePairCode() {
    // parentId no longer needs to be passed in — the backend reads it
    // from the authenticated session, not from the request body. (A
    // client-supplied parentId would just be an IDOR waiting to happen.)
    return request("/pairing/generate", { method: "POST" });
  },

  async registerChild({ name, username, password, pairCode }) {
    return request("/auth/register-child", {
      method: "POST",
      body: { name, username, password, pairCode },
    });
  },

  // ---------------------------------------------------------------------
  // The following four still hit endpoints that don't exist yet — that's
  // the next build step (transactions + approvals blueprints). Wiring
  // them now so the shape is locked in; they'll work as soon as those
  // routes exist, no frontend changes needed.
  // ---------------------------------------------------------------------

  async getFamily() {
    return request("/auth/family");
  },

  async getTransactions() {
    return request("/transactions");
  },

  async createTransaction({ amount, merchant, note }) {
    return request("/transactions", { method: "POST", body: { amount, merchant, note } });
  },

  async updateTransaction({ txId, amount, merchant, note }) {
    return request(`/transactions/${txId}`, { method: "PUT", body: { amount, merchant, note } });
  },

  async cancelTransaction(txId) {
    return request(`/transactions/${txId}/cancel`, { method: "POST" });
  },

  async uploadReceipt(txId, file) {
    const form = new FormData();
    form.append("receipt", file);
    return requestForm(`/transactions/${txId}/receipt`, form);
  },

  receiptUrl(txId) {
    return `${BASE_URL}/api/transactions/${txId}/receipt`;
  },

  async decideTransaction({ txId, decision }) {
    // decision: "approved" | "denied"
    const action = decision === "approved" ? "approve" : "deny";
    return request(`/transactions/${txId}/${action}`, { method: "POST" });
  },

  async getUserById(id) {
    return request(`/users/${id}`);
  },

  async updateProfile({ name, avatarUrl }) {
    return request("/users/me", { method: "PUT", body: { name, avatarUrl } });
  },

  async updateChildControls({ childId, balanceLimit, walletBalance }) {
    return request(`/users/children/${childId}/controls`, {
      method: "PUT",
      body: { balanceLimit, walletBalance },
    });
  },

  async getNotifications() {
    return request("/users/me/notifications");
  },

  async markNotificationsRead() {
    return request("/users/me/notifications/read", { method: "POST" });
  },

  async getComments(txId) {
    return request(`/transactions/${txId}/comments`);
  },

  async addComment(txId, body) {
    return request(`/transactions/${txId}/comments`, { method: "POST", body: { body } });
  },
};
