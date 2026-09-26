import React, { useState } from 'react';
import { X, CheckCircle, XCircle, ShieldAlert, Sparkles } from 'lucide-react';
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
  const [editedBody, setEditedBody] = useState(
    approval.type === 'reply_draft'
      ? approval.payload?.draft_body || ''
      : ''
  );
  const [submitting, setSubmitting] = useState(false);

  const handleAction = async (status: 'approved' | 'rejected') => {
    setSubmitting(true);
    try {
      const payload = { ...approval.payload };
      if (approval.type === 'reply_draft' && editedBody) {
        payload.draft_body = editedBody;
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
        return 'Approve First Send of New A/B Variants';
      case 'kill_variant':
        return 'Approve Self-Healing Variant Kill & Reallocation';
      case 'reply_draft':
        return 'Approve AI-Drafted Prospect Reply';
      case 'voice_escalation':
        return 'Approve Voice Escalation Call';
      default:
        return 'Human-in-the-Loop Gate Approval';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">{getTitle()}</h3>
              <p className="text-xs text-slate-400">Strict governance gate: Agent paused awaiting human sign-off</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Detail presentation depending on type */}
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

          {approval.type === 'kill_variant' && (
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 space-y-2">
              <div className="text-xs font-bold text-rose-400">Underperforming Variant Flagged for Termination</div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {approval.payload?.reasoning}
              </p>
              <div className="pt-2 text-[11px] text-slate-400">
                Approving will immediately reallocate sequence traffic and instruct LLM to generate Variant C using winning angle telemetry.
              </div>
            </div>
          )}

          {approval.type === 'send_new_variant' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-300">
                The agent has formulated 2 contrasting copy angles using your reference emails. Review subjects below:
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <span className="text-[11px] font-bold text-indigo-400 block mb-1">Variant A (Pain Point)</span>
                  <div className="text-xs font-semibold text-white">{approval.payload?.variant_a?.subject}</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <span className="text-[11px] font-bold text-purple-400 block mb-1">Variant B (ROI / Metrics)</span>
                  <div className="text-xs font-semibold text-white">{approval.payload?.variant_b?.subject}</div>
                </div>
              </div>
            </div>
          )}

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
              placeholder="e.g. Looks good, approved for live sequence."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-800/30 flex items-center justify-between">
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
