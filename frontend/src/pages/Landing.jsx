// src/pages/Landing.jsx
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Mark from "../components/Mark";
import { Button, Eyebrow } from "../components/ui";
import { formatRupees } from "../lib/money";

export default function Landing() {
  return (
    <div className="min-h-screen bg-parchment grain-overlay overflow-hidden relative">
      <header className="max-w-5xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-ink">
          <Mark size={26} />
          <span className="font-display text-lg tracking-tight">Family Pocket</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm font-semibold text-ink/70 hover:text-ink">
            Sign in
          </Link>
          <Button as={Link} to="/register" variant="brass" className="!py-2.5">
            Get started
          </Button>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-6 pt-14 pb-20 grid md:grid-cols-2 gap-14 items-center">
        <div>
          <Eyebrow>A simple pocket-money app for two</Eyebrow>
          <h1 className="font-display text-5xl md:text-6xl leading-[1.05] mt-4 text-ink">
            Every request
            <br />
            gets a quick
            <br />
            yes or no.
          </h1>
          <p className="mt-6 text-slate/80 text-lg leading-relaxed max-w-md">
            A parent starts the account and shares a code with the child. After that,
            every request waits for a simple approval before it is spent.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Button as={Link} to="/register" variant="primary">
              Register as a parent
            </Button>
            <Button as={Link} to="/register-child" variant="ghost">
              I have a pairing code
            </Button>
          </div>
        </div>

        <LedgerHero />
      </section>

      <section className="max-w-5xl mx-auto px-6 pb-24 grid sm:grid-cols-3 gap-6">
        {[
          {
            t: "Join once",
            d: "The parent makes one code. The child uses it to join the account.",
          },
          {
            t: "Send a request",
            d: "The child enters an amount, a shop name, and a short note. It goes in as pending.",
          },
          {
            t: "Make a call",
            d: "The parent approves or rejects it with one click. The child sees the result right away.",
          },
        ].map((f, i) => (
          <motion.div
            key={f.t}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
            className="bg-white/50 border border-ink/10 rounded-xl p-6"
          >
            <h3 className="font-display text-xl text-ink mb-2">{f.t}</h3>
            <p className="text-sm text-slate/70 leading-relaxed">{f.d}</p>
          </motion.div>
        ))}
      </section>
    </div>
  );
}

function LedgerHero() {
  // The page's signature moment: a mock ledger card that animates a
  // pending request being sealed "Approved" on load, then loops gently.
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      <div className="bg-white rounded-2xl shadow-card border border-ink/10 p-6 ledger-rule">
        <div className="flex items-center justify-between mb-5">
          <Eyebrow>Pending request</Eyebrow>
          <span className="font-mono text-xs text-slate/40">#A14-902</span>
        </div>
        <div className="flex items-center justify-between mb-1">
          <span className="font-display text-2xl text-ink">{formatRupees(2400)}</span>
          <motion.div
            initial={{ scale: 0, rotate: -20, opacity: 0 }}
            animate={{ scale: 1, rotate: -8, opacity: 1 }}
            transition={{ delay: 1.1, type: "spring", stiffness: 260, damping: 16 }}
            className="w-16 h-16 rounded-full bg-sage/90 border-[3px] border-sage flex items-center justify-center shadow-seal"
          >
            <span className="font-display text-parchment text-[9px] tracking-widest uppercase">
              Ok
            </span>
          </motion.div>
        </div>
        <p className="text-sm text-slate/60 mb-4">Local bakery · "Birthday cake for Aanya 🎂"</p>
        <div className="flex items-center gap-2 text-xs text-slate/40 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-sage" />
          Filed by Aarav · Approved by Priya
        </div>
      </div>
      <div className="absolute -bottom-6 -right-6 w-full h-full bg-brass/10 rounded-2xl -z-10" />
    </motion.div>
  );
}
