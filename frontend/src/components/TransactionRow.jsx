import { motion } from "framer-motion";
import { useState } from "react";
import SealStamp from "./SealStamp";
import { Button, Input } from "./ui";
import { formatRupees } from "../lib/money";
import { api } from "../lib/api";

const statusCopy = {
  pending: "Waiting for approval",
  approved: "Approved",
  denied: "Rejected",
  canceled: "Canceled",
};

export default function TransactionRow({
  tx,
  childName,
  showActions,
  onDecide,
  deciding,
  canEdit,
  onEdit,
  onCancel,
  onUploadReceipt,
}) {
  const [openComments, setOpenComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [comment, setComment] = useState("");
  const [commentError, setCommentError] = useState("");
  const [loadingComments, setLoadingComments] = useState(false);

  async function toggleComments() {
    const next = !openComments;
    setOpenComments(next);
    if (next && comments.length === 0) {
      setLoadingComments(true);
      setCommentError("");
      try {
        setComments(await api.getComments(tx.id));
      } catch (err) {
        setCommentError(err.message);
      } finally {
        setLoadingComments(false);
      }
    }
  }

  async function submitComment(e) {
    e.preventDefault();
    if (!comment.trim()) return;
    setCommentError("");
    try {
      const next = await api.addComment(tx.id, comment);
      setComments(next);
      setComment("");
    } catch (err) {
      setCommentError(err.message);
    }
  }

  return (
    <motion.div layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
      <div className="flex items-center gap-4 py-4 px-1 border-b border-ink/8 last:border-0">
        <SealStamp status={tx.status} />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="font-display text-xl text-ink">{formatRupees(tx.amount)}</span>
            <span className="text-sm text-slate/70">{tx.merchant}</span>
            {childName && <span className="text-xs font-mono text-slate/40">- {childName}</span>}
            {tx.hasReceipt && (
              <a
                href={api.receiptUrl(tx.id)}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-brassdark hover:text-ink"
              >
                Receipt
              </a>
            )}
          </div>
          {tx.note && <p className="text-sm text-slate/60 mt-0.5 truncate">"{tx.note}"</p>}
          <p className="text-xs font-mono text-slate/35 mt-1">
            {statusCopy[tx.status]} -{" "}
            {new Date(tx.createdAt).toLocaleString(undefined, {
              month: "short",
              day: "numeric",
              hour: "numeric",
              minute: "2-digit",
            })}
          </p>
          <button
            type="button"
            onClick={toggleComments}
            className="text-xs font-semibold text-slate/50 hover:text-ink mt-2"
          >
            {openComments ? "Hide comments" : "Comments"}
          </button>
        </div>

        {canEdit && tx.status === "pending" && (
          <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
            <Button variant="ghost" className="!px-3 !py-2 !text-xs" onClick={() => onEdit(tx)}>
              Edit
            </Button>
            <label className="inline-flex items-center justify-center font-semibold text-xs px-3 py-2 rounded-md border border-ink/20 hover:border-ink/50 cursor-pointer">
              Receipt
              <input
                className="hidden"
                type="file"
                accept="image/png,image/jpeg,application/pdf"
                onChange={(e) => e.target.files?.[0] && onUploadReceipt(tx.id, e.target.files[0])}
              />
            </label>
            <Button variant="deny" className="!px-3 !py-2 !text-xs" onClick={() => onCancel(tx.id)}>
              Cancel
            </Button>
          </div>
        )}

        {showActions && tx.status === "pending" && (
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="approve"
              className="!px-4 !py-2 !text-xs"
              disabled={deciding}
              onClick={() => onDecide(tx.id, "approved")}
            >
              Approve
            </Button>
            <Button
              variant="deny"
              className="!px-4 !py-2 !text-xs"
              disabled={deciding}
              onClick={() => onDecide(tx.id, "denied")}
            >
              Deny
            </Button>
          </div>
        )}
      </div>

      {openComments && (
        <div className="ml-14 mr-1 mb-4 rounded-md bg-white/45 border border-ink/10 p-3">
          {loadingComments ? (
            <p className="text-xs text-slate/50">Loading comments...</p>
          ) : comments.length === 0 ? (
            <p className="text-xs text-slate/50">No comments yet.</p>
          ) : (
            <div className="space-y-2 mb-3">
              {comments.map((c) => (
                <div key={c.id} className="text-sm">
                  <span className="font-semibold text-ink">{c.authorName}</span>
                  <span className="text-xs text-slate/40"> {c.authorRole}</span>
                  <p className="text-slate/70">{c.body}</p>
                </div>
              ))}
            </div>
          )}
          {commentError && <p className="text-xs text-rust mb-2">{commentError}</p>}
          <form onSubmit={submitComment} className="flex gap-2">
            <Input
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add a note"
              maxLength={500}
            />
            <Button type="submit" variant="ghost" className="!px-3 !py-2">
              Send
            </Button>
          </form>
        </div>
      )}
    </motion.div>
  );
}
