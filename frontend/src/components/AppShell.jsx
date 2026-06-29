import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Mark from "./Mark";
import { Button, Input } from "./ui";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";

export default function AppShell({ children }) {
  const { user, logout, setUser } = useAuth();
  const navigate = useNavigate();
  const [panelOpen, setPanelOpen] = useState(false);
  const [profile, setProfile] = useState({ name: user?.name || "", avatarUrl: user?.avatar_url || "" });
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    if (!user) return;
    setProfile({ name: user.name || "", avatarUrl: user.avatar_url || "" });
    api.getNotifications().then(setNotifications).catch(() => setNotifications([]));
  }, [user]);

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  async function saveProfile(e) {
    e.preventDefault();
    const updated = await api.updateProfile(profile);
    setUser(updated);
  }

  async function markRead() {
    await api.markNotificationsRead();
    setNotifications((items) => items.map((item) => ({ ...item, read: true })));
  }

  const unread = notifications.filter((n) => !n.read).length;

  return (
    <div className="min-h-screen bg-parchment grain-overlay relative">
      <header className="border-b border-ink/10 bg-parchment/90 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-ink">
            <Mark size={26} />
            <span className="font-display text-lg tracking-tight">Family Pocket</span>
          </Link>
          {user && (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setPanelOpen((open) => !open)}
                className="inline-flex items-center gap-2 text-sm text-slate/70 hover:text-ink transition-colors"
              >
                {user.avatar_url && (
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="h-7 w-7 rounded-full object-cover border border-ink/15"
                  />
                )}
                <span className="hidden sm:inline">
                  {user.role === "parent" ? "Parent" : "Child"} - {user.name}
                </span>
                {unread > 0 && (
                  <span className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-rust px-1.5 text-xs text-white">
                    {unread}
                  </span>
                )}
              </button>
              <button
                onClick={handleLogout}
                className="text-xs font-semibold uppercase tracking-wide text-slate/60 hover:text-rust transition-colors"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
        {user && panelOpen && (
          <div className="border-t border-ink/10 bg-parchment">
            <div className="max-w-5xl mx-auto px-6 py-5 grid md:grid-cols-2 gap-6">
              <form onSubmit={saveProfile} className="grid gap-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-brassdark">Profile</p>
                <Input
                  label="Display name"
                  value={profile.name}
                  onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
                />
                <Input
                  label="Avatar URL"
                  value={profile.avatarUrl}
                  onChange={(e) => setProfile((p) => ({ ...p, avatarUrl: e.target.value }))}
                  placeholder="https://example.com/avatar.png"
                />
                <Button type="submit" variant="ghost" className="justify-self-start !py-2">
                  Save profile
                </Button>
              </form>

              <div>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-brassdark">Notifications</p>
                  {notifications.length > 0 && (
                    <button onClick={markRead} className="text-xs font-semibold text-slate/50 hover:text-ink">
                      Mark read
                    </button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <p className="text-sm text-slate/55 mt-3">No notifications yet.</p>
                ) : (
                  <ul className="mt-3 space-y-2 max-h-48 overflow-auto pr-2">
                    {notifications.map((item) => (
                      <li key={item.id} className="text-sm text-slate/70">
                        <span className={item.read ? "text-slate/40" : "font-semibold text-ink"}>
                          {item.message}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}
      </header>
      <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
    </div>
  );
}
