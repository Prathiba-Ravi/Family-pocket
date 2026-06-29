// src/components/ui.jsx
import { motion } from "framer-motion";

export function Button({ as = "button", variant = "primary", className = "", children, ...props }) {
  const base =
    "inline-flex items-center justify-center gap-2 font-sans font-semibold text-sm px-5 py-3 rounded-md transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-ink text-parchment hover:bg-inkdeep",
    brass: "bg-brass text-ink hover:bg-brassdark",
    ghost: "bg-transparent text-ink border border-ink/20 hover:border-ink/50",
    approve: "bg-sage text-parchment hover:bg-[#4d7458]",
    deny: "bg-transparent text-rust border border-rust/40 hover:bg-rust/10",
  };
  const isNativeTag = typeof as === "string";
  const Comp = isNativeTag ? motion[as] || motion.button : as;
  const motionProps = isNativeTag ? { whileTap: { scale: 0.97 } } : {};
  return (
    <Comp
      {...motionProps}
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </Comp>
  );
}

export function Input({ label, error, className = "", ...props }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-xs font-semibold uppercase tracking-wide text-slate/70 mb-1.5">
          {label}
        </span>
      )}
      <input
        className={`w-full bg-white/70 border border-ink/15 rounded-md px-4 py-3 text-sm text-ink placeholder:text-slate/40 focus:border-brass focus:bg-white transition-colors ${className}`}
        {...props}
      />
      {error && <span className="block text-xs text-rust mt-1.5">{error}</span>}
    </label>
  );
}

export function Card({ className = "", children, ...props }) {
  return (
    <div className={`bg-parchment border border-ink/10 rounded-xl shadow-card ${className}`} {...props}>
      {children}
    </div>
  );
}

export function Eyebrow({ children }) {
  return (
    <span className="font-mono text-[11px] uppercase tracking-[0.25em] text-brassdark">
      {children}
    </span>
  );
}
