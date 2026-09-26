import React, { useState } from 'react';
import { X, CheckCircle, XCircle, ShieldAlert, Sparkles, Layers, FileText } from 'lucide-react';
import { Approval } from '../types';

interface ApprovalModalProps {
  approval: Approval | null;
  onClose: () => void;
  onResolve: (id: string, status: 'approved' | 'rejected', notes?: string, editedPayload?: any) => Promise<void>;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  approval,
  onClose,
  onResolve,
}) => {
  if (!approval) return null;

  const [notes, setNotes] = useState('');

  // Variant A & B editable states for 'send_new_variant'
  const [varASubject, setVarASubject] = useState(approval.payload?.variant_a?.subject || '');
  const [varABody, setVarABody] = useState(approval.payload?.variant_a?.body_template || '');
  const [varBSubject, setVarBSubject] = useState(approval.payload?.variant_b?.subject || '');
  const [varBBody, setVarBBody] = useState(approval.payload?.variant_b?.body_template || '');
  const [viewMode, setViewMode] = useState<'split' | 'tabA' | 'tabB'>('split');

  // Variant C editable state
  const [editedSubject, setEditedSubject] = useState(
    approval.type === 'send_replacement_variant'
      ? approval.payload?.variant_c?.subject || ''
      : ''
  );
  const [editedBody, setEditedBody] = useState(
    approval.type === 'reply_draft'
      ? approval.payload?.draft_body || ''
      : approval.type === 'send_replacement_variant'
      ? approval.payload?.variant_c?.body_template || ''
      : ''
  );
  const [submitting, setSubmitting] = useState(false);

  const handleAction = async (status: 'approved' | 'rejected') => {
    setSubmitting(true);
    try {
      const payload = { ...approval.payload };

      if (approval.type === 'send_new_variant') {
        payload.variant_a = {
          ...approval.payload?.variant_a,
          subject: varASubject,
          body_template: varABody,
        };
        payload.variant_b = {
          ...approval.payload?.variant_b,
          subject: varBSubject,
          body_template: varBBody,
        };
      }

      if (approval.type === 'reply_draft' && editedBody) {
        payload.draft_body = editedBody;
      }
      if (approval.type === 'send_replacement_variant') {
        if (editedSubject) payload.subject = editedSubject;
        if (editedBody) payload.body_template = editedBody;
      }

      await onResolve(approval.id, status, notes, payload);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  const getTitle = () => {
    switch (approval.type) {
      case 'send_new_variant':
        return 'Approve First Send of New A/B Pitch Variants';
      case 'kill_variant':
        return 'Approve Self-Healing Variant Kill & Reallocation';
      case 'send_replacement_variant':
        return 'Approve Evolved Variant C (Mutant Challenger)';
      case 'reply_draft':
        return 'Approve AI-Drafted Prospect Reply';
      case 'voice_escalation':
        return 'Approve Voice Escalation Call';
      default:
        return 'Human-in-the-Loop Gate Approval';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 my-6">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{getTitle()}</h3>
              <p className="text-xs text-slate-400">Section 9 Governance Gate: Inspect, refine, or approve complete copies before launch.</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* SEND_NEW_VARIANT: Full Body & Subject Inspection & Editing */}
          {approval.type === 'send_new_variant' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs">
                <div className="flex items-center gap-2 text-indigo-300 font-medium">
                  <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span>The agent formulated 2 contrasting copy angles. Review full subject lines & email bodies below:</span>
                </div>
                <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-lg self-start sm:self-auto">
                  <button
                    type="button"
                    onClick={() => setViewMode('split')}
                    className={`px-2.5 py-1 rounded text-[11px] font-semibold transition ${
                      viewMode === 'split' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('tabA')}
                    className={`px-2.5 py-1 rounded text-[11px] font-semibold transition ${
                      viewMode === 'tabA' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Variant A
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('tabB')}
                    className={`px-2.5 py-1 rounded text-[11px] font-semibold transition ${
                      viewMode === 'tabB' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Variant B
                  </button>
                </div>
              </div>

              {/* Side-by-Side or Selected Tab Container */}
              <div className={`grid gap-4 ${viewMode === 'split' ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
                {/* Variant A */}
                {(viewMode === 'split' || viewMode === 'tabA') && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-indigo-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                        <span className="text-xs font-bold text-indigo-300 uppercase tracking-wide">
                          Variant A (Pain Point Hook)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                        50% Initial Traffic
                      </span>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 mb-1">Subject Line (Editable):</label>
                      <input
                        type="text"
                        value={varASubject}
                        onChange={(e) => setVarASubject(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-[11px] font-semibold text-slate-300">Full Email Body (Editable):</label>
                        <span className="text-[10px] text-slate-400 font-mono">{varABody.length} chars</span>
                      </div>
                      <textarea
                        rows={9}
                        value={varABody}
                        onChange={(e) => setVarABody(e.target.value)}
                        className="w-full p-3 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans leading-relaxed resize-y"
                      />
                      <div className="text-[10px] text-slate-400 mt-1">
                        Merge tags supported: <code className="text-indigo-300 font-mono">{"{name}"}</code>, <code className="text-indigo-300 font-mono">{"{company}"}</code>, <code className="text-indigo-300 font-mono">{"{title}"}</code>
                      </div>
                    </div>
                  </div>
                )}

                {/* Variant B */}
                {(viewMode === 'split' || viewMode === 'tabB') && (
                  <div className="p-4 rounded-xl bg-slate-950/70 border border-purple-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
                        <span className="text-xs font-bold text-purple-300 uppercase tracking-wide">
                          Variant B (ROI & Benchmark Hook)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">
                        50% Initial Traffic
                      </span>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-300 mb-1">Subject Line (Editable):</label>
                      <input
                        type="text"
                        value={varBSubject}
                        onChange={(e) => setVarBSubject(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-purple-500 font-medium"
                      />
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block text-[11px] font-semibold text-slate-300">Full Email Body (Editable):</label>
                        <span className="text-[10px] text-slate-400 font-mono">{varBBody.length} chars</span>
                      </div>
                      <textarea
                        rows={9}
                        value={varBBody}
                        onChange={(e) => setVarBBody(e.target.value)}
                        className="w-full p-3 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-sans leading-relaxed resize-y"
                      />
                      <div className="text-[10px] text-slate-400 mt-1">
                        Merge tags supported: <code className="text-purple-300 font-mono">{"{name}"}</code>, <code className="text-purple-300 font-mono">{"{company}"}</code>, <code className="text-purple-300 font-mono">{"{title}"}</code>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* REPLY_DRAFT */}
          {approval.type === 'reply_draft' && (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-slate-800/60 text-xs text-slate-300">
                <span className="font-semibold text-white">To:</span> {approval.payload?.to_name} ({approval.payload?.to_email}) at {approval.payload?.company}
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  AI Drafted Reply (You can edit directly before sending):
                </label>
                <textarea
                  rows={6}
                  value={editedBody}
                  onChange={(e) => setEditedBody(e.target.value)}
                  className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                />
              </div>
            </div>
          )}

          {/* KILL_VARIANT */}
          {approval.type === 'kill_variant' && (
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 space-y-2">
              <div className="text-xs font-bold text-rose-400">Underperforming Variant Flagged for Termination</div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {approval.payload?.reasoning}
              </p>
              <div className="pt-2 text-[11px] text-slate-400">
                Approving will immediately terminate the loser variant, shift 100% sequence traffic to the winning variant, and trigger Variant C mutant challenger review.
              </div>
            </div>
          )}

          {/* SEND_REPLACEMENT_VARIANT */}
          {approval.type === 'send_replacement_variant' && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 space-y-1.5">
                <div className="flex items-center gap-1.5 text-indigo-400 text-xs font-bold">
                  <Sparkles className="w-4 h-4" />
                  <span>Evolution Strategy Rationale</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {approval.payload?.evolution_rationale || "Synthesized from winning hook telemetry and campaign reference styles."}
                </p>
                <div className="text-[11px] text-slate-400 pt-1">
                  Iterated upon Parent Winner: <span className="font-mono text-indigo-300 font-semibold">{approval.payload?.parent_winner_id?.slice(0, 8)}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Variant C Subject Line (Editable):
                </label>
                <input
                  type="text"
                  value={editedSubject}
                  onChange={(e) => setEditedSubject(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Variant C Body Template (Editable):
                </label>
                <textarea
                  rows={6}
                  value={editedBody}
                  onChange={(e) => setEditedBody(e.target.value)}
                  className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans leading-relaxed"
                />
              </div>

              <div className="text-[11px] text-slate-400">
                Approving will activate Variant C alongside the champion variant with an initial 50/50 traffic split.
              </div>
            </div>
          )}

          {/* VOICE_ESCALATION */}
          {approval.type === 'voice_escalation' && (
            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 space-y-2">
              <div className="text-xs font-bold text-indigo-400">Hot Lead Intent Threshold Triggered</div>
              <p className="text-xs text-slate-300">
                Prospect {approval.payload?.contact_name} at {approval.payload?.company} reached intent score {approval.payload?.intent_score}.
              </p>
              <div className="text-[11px] text-slate-400">
                Badge: "Voice escalation: logic complete — awaiting connected number"
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">
              Approval Notes / Feedback (Optional):
            </label>
            <input
              type="text"
              placeholder="e.g. Approved for live sequence dispatch."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <button
            disabled={submitting}
            onClick={() => handleAction('rejected')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold transition"
          >
            <XCircle className="w-4 h-4" />
            <span>Reject</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              disabled={submitting}
              onClick={() => handleAction('approved')}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition"
            >
              <CheckCircle className="w-4 h-4" />
              <span>{submitting ? 'Executing...' : 'Approve & Execute'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
