import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';
import { Approval } from '../types';

interface ApprovalsProps {
  approvals: Approval[];
  onOpenApprovalModal: (approval: Approval) => void;
  onQuickResolve: (id: string, status: 'approved' | 'rejected') => Promise<void>;
}

export const Approvals: React.FC<ApprovalsProps> = ({
  approvals,
  onOpenApprovalModal,
  onQuickResolve,
}) => {
  const [filter, setFilter] = useState<'pending' | 'resolved'>('pending');

  const pending = approvals.filter((a) => a.status === 'pending');
  const resolved = approvals.filter((a) => a.status !== 'pending');
  const displayed = filter === 'pending' ? pending : resolved;

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'send_new_variant':
        return 'First Send of New A/B Variant';
      case 'kill_variant':
        return 'Kill Underperforming Variant';
      case 'reply_draft':
        return 'Inbound Reply AI Draft';
      case 'voice_escalation':
        return 'Voice Escalation Call';
      default:
        return type.replace('_', ' ');
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            Human-in-the-Loop Governance Queue
            {pending.length > 0 && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold animate-pulse">
                {pending.length} Action{pending.length > 1 ? 's' : ''} Required
              </span>
            )}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Section 9 HITL Gates: Critical actions (first sends, copy changes, variant termination, AI replies) pause for human sign-off.
          </p>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 self-start">
          <button
            onClick={() => setFilter('pending')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filter === 'pending'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Pending ({pending.length})
          </button>
          <button
            onClick={() => setFilter('resolved')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filter === 'resolved'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Resolved History ({resolved.length})
          </button>
        </div>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {displayed.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 rounded-2xl bg-slate-900 border border-slate-800">
            {filter === 'pending' ? 'No pending approvals. All autonomous systems operating smoothly!' : 'No resolved approvals history yet.'}
          </div>
        ) : (
          displayed.map((a) => {
            const isPending = a.status === 'pending';
            const isApproved = a.status === 'approved';

            return (
              <div
                key={a.id}
                className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                        isPending
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : isApproved
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                        {getTypeLabel(a.type)}
                      </h3>
                      <div className="text-[11px] text-slate-400">
                        Created {new Date(a.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-full border self-start sm:self-auto ${
                      isPending
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse'
                        : isApproved
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    }`}
                  >
                    {a.status.toUpperCase()}
                  </span>
                </div>

                {/* Payload Preview */}
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
                  {a.type === 'reply_draft' && (
                    <div className="space-y-1">
                      <div><strong className="text-white">To:</strong> {a.payload?.to_name} at {a.payload?.company}</div>
                      <div className="text-slate-400 italic line-clamp-2">"{a.payload?.draft_body}"</div>
                    </div>
                  )}

                  {a.type === 'kill_variant' && (
                    <div>
                      <strong className="text-white">Reason:</strong> {a.payload?.reasoning}
                    </div>
                  )}

                  {a.type === 'send_new_variant' && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <div><strong className="text-white">A/B Testing Strategy:</strong> {a.payload?.strategy}</div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold">50/50 Traffic Split</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-indigo-500/20">
                          <span className="font-bold text-indigo-300 block truncate">A: {a.payload?.variant_a?.subject}</span>
                          <p className="text-slate-400 line-clamp-2 mt-1 leading-relaxed">{a.payload?.variant_a?.body_template}</p>
                        </div>
                        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-purple-500/20">
                          <span className="font-bold text-purple-300 block truncate">B: {a.payload?.variant_b?.subject}</span>
                          <p className="text-slate-400 line-clamp-2 mt-1 leading-relaxed">{a.payload?.variant_b?.body_template}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {a.type === 'voice_escalation' && (
                    <div>
                      <strong className="text-white">Hot Prospect:</strong> {a.payload?.contact_name} (Intent: {a.payload?.intent_score})
                    </div>
                  )}
                </div>

                {/* Actions */}
                {isPending && (
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => onQuickResolve(a.id, 'rejected')}
                      className="px-3.5 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => onOpenApprovalModal(a)}
                      className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
                    >
                      Review & Edit
                    </button>
                    <button
                      onClick={() => onQuickResolve(a.id, 'approved')}
                      className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition"
                    >
                      1-Click Approve
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
