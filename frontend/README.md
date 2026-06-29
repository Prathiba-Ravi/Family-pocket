# Guardian Ledger — Frontend

A parent/child transaction-approval app. Parent registers first, generates a
one-time pairing code, child redeems it to register, child files spend
requests, parent approves or denies ("seals" or "voids") them.

This is the **frontend only**, wired to a mock localStorage "API" in
`src/lib/api.js` so it's fully clickable right now. Every function in that
file mirrors what real REST calls will look like, so swapping in your
Python backend later is mostly find-and-replace.

## Stack
- React 18 + Vite
- React Router (client-side routing)
- Tailwind CSS (design tokens in `tailwind.config.js`)
- Framer Motion (the seal-stamp animation, page transitions)

## Folder structure
```
guardian-ledger/
├── index.html
├── tailwind.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx                  # routes
│   ├── index.css                # global styles, grain texture, a11y
│   ├── context/
│   │   └── AuthContext.jsx      # current user, login/register/logout
│   ├── lib/
│   │   └── api.js               # MOCK BACKEND — replace with real fetch calls
│   ├── components/
│   │   ├── AppShell.jsx         # top nav for logged-in pages
│   │   ├── ProtectedRoute.jsx   # role-based route guard
│   │   ├── SealStamp.jsx        # the signature approve/deny animation
│   │   ├── TransactionRow.jsx
│   │   ├── Mark.jsx             # logo glyph
│   │   └── ui.jsx               # Button, Input, Card, Eyebrow
│   └── pages/
│       ├── Landing.jsx
│       ├── RegisterParent.jsx
│       ├── RegisterChild.jsx
│       ├── Login.jsx
│       ├── ParentDashboard.jsx
│       └── ChildDashboard.jsx
```

## Run it
```
npm install
npm run dev
```
Open the printed localhost URL. Register as a parent, generate a code,
open an incognito window (or log out), register as a child with that code,
and file a request — it'll show up live on the parent's dashboard on refresh.

## Step-by-step plan to finish the whole project

**1. Frontend (done here)**
- [x] Auth flows: parent register, child register-by-code, login
- [x] Parent dashboard: generate pairing code, view family, approve/deny
- [x] Child dashboard: file request, see pending/decided history
- [ ] Polish: toast notifications instead of silent refresh, pagination for
      long transaction history, child spend-limit display

**2. Design the real data model** (before writing backend code)
- `users`: id, role, name, username, password_hash, parent_id (nullable)
- `pair_codes`: code, parent_id, expires_at, used (bool)
- `transactions`: id, child_id, amount, merchant, note, status, created_at, decided_at

**3. Build the Python backend**
- Pick Flask or FastAPI. Suggested endpoints are documented as comments at
  the top of `src/lib/api.js` — build those one-for-one.
- Use a real database (SQLite is fine to start) instead of localStorage.
- Add session/JWT auth and replace `AuthContext`'s calls to `api.js` with
  real `fetch()` calls to your backend. Keep the function signatures the
  same (`registerParent`, `login`, `generatePairCode`, etc.) so almost no
  page code needs to change.
- Enforce role checks server-side (a child hitting the approve endpoint
  directly should fail, not just be hidden in the UI).

**4. Wire frontend to backend**
- Add a `VITE_API_URL` env var, point `fetch` calls at it.
- Handle real network errors and loading states (the mock API already
  simulates latency so your UI is ready for this).

**5. Deliberately introduce and then study vulnerabilities**
Since the goal is to demonstrate web vulnerabilities, good candidates to
build into the *backend* (and then fix one at a time) once it exists:
- Broken access control — child role can call `/approve` directly via curl
- IDOR — parent A can approve parent B's child's transaction by guessing IDs
- Pairing code that doesn't expire or isn't single-use (race condition demo)
- Storing passwords in plaintext or with weak hashing
- No rate limiting on login (brute force demo) or pairing-code guessing
- Missing CSRF protection on the approve/deny POST routes
- Reflected/stored XSS in the `note` or `merchant` free-text fields
- JWT with no expiry or a guessable secret

Build each vulnerability behind a feature flag or git branch so you can
demo "vulnerable" vs. "patched" side by side.

**6. Write up the findings**
Document each vuln: how it was introduced, how to exploit it (request/
response examples), the impact, and the fix — that write-up is usually the
actual deliverable for this kind of project.

## Notes on the mock API
- Data persists in `localStorage` under the key `gl_db_v1`. Clear it with
  `localStorage.clear()` in devtools to reset all users/transactions.
- Passwords are stored in plaintext in `api.js` — that's fine for a frontend
  demo, but obviously don't carry that pattern into the real backend.
