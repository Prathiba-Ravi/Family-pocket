// src/components/SealStamp.jsx
import { motion, AnimatePresence } from "framer-motion";

// The status badge for each request.
export default function SealStamp({ status }) {
  return (
    <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
      <AnimatePresence>
        {status === "approved" && (
          <motion.div
            key="approved"
            initial={{ scale: 2.4, opacity: 0, rotate: -8 }}
            animate={{ scale: 1, opacity: 1, rotate: -6 }}
            transition={{ type: "spring", stiffness: 500, damping: 18 }}
            className="absolute w-14 h-14 rounded-full bg-sage/90 border-[3px] border-sage flex items-center justify-center shadow-seal"
          >
            <span className="font-display text-parchment text-[10px] tracking-widest uppercase rotate-[-6deg]">
              Approved
            </span>
            <motion.div
              initial={{ scale: 0.4, opacity: 0.6 }}
              animate={{ scale: 1.9, opacity: 0 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              className="absolute inset-0 rounded-full border-2 border-sage"
            />
          </motion.div>
        )}
        {status === "denied" && (
          <motion.div
            key="denied"
            initial={{ y: -40, opacity: 0, rotate: 0 }}
            animate={{ y: 0, opacity: 1, rotate: -10 }}
            transition={{ type: "spring", stiffness: 400, damping: 14 }}
            className="absolute w-16 h-10 border-[3px] border-rust rounded-sm flex items-center justify-center"
          >
            <span className="font-display text-rust text-[11px] tracking-[0.2em] uppercase">
              Rejected
            </span>
          </motion.div>
        )}
        {status === "pending" && (
          <motion.div
            key="pending"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 6, ease: "linear" }}
            className="w-10 h-10 rounded-full border-2 border-dashed border-brass/60"
          />
        )}
        {status === "canceled" && (
          <motion.div
            key="canceled"
            initial={{ opacity: 0, rotate: 8 }}
            animate={{ opacity: 1, rotate: 4 }}
            className="absolute w-16 h-10 border-[3px] border-slate/35 rounded-sm flex items-center justify-center"
          >
            <span className="font-display text-slate/55 text-[10px] tracking-[0.18em] uppercase">
              Canceled
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
