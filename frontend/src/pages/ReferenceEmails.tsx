import React, { useState } from 'react';
import { MailCheck, Plus, Trash2, Sparkles, BookOpen } from 'lucide-react';
import { ReferenceEmail } from '../types';

interface ReferenceEmailsProps {
  referenceEmails: ReferenceEmail[];
  onAddEmail: (subject: string, body: string, notes?: string) => Promise<void>;
  onDeleteEmail: (id: string) => Promise<void>;
}

export const ReferenceEmails: React.FC<ReferenceEmailsProps> = ({
  referenceEmails,
  onAddEmail,
  onDeleteEmail,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;
    setSubmitting(true);
    try {
      await onAddEmail(subject, body, notes);
      setIsModalOpen(false);
      setSubject('');
      setBody('');
      setNotes('');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            Reference Emails & Few-Shot Pool
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
              Training Knowledge Base
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Proven cold outreach copy used by the LLM variant generator as few-shot training examples to calibrate tone, length, and hooks.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add Winning Email Copy</span>
        </button>
      </div>

      {/* Grid of Reference Emails */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {referenceEmails.map((email) => (
          <div
            key={email.id}
            className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm space-y-4 hover:border-slate-700 transition flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">
                    Proven Template Subject:
                  </span>
                  <h3 className="text-sm font-bold text-white leading-snug">{email.subject}</h3>
                </div>
                <button
                  onClick={() => onDeleteEmail(email.id)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                  title="Remove from training pool"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 font-sans whitespace-pre-line leading-relaxed">
                {email.body}
              </div>
            </div>

            {email.style_notes && (
              <div className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/15 text-[11px] text-indigo-300 flex items-start gap-2">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Style Rationale:</strong> {email.style_notes}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Add Winning Reference Copy</h3>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Subject Line</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Quick question regarding outbound deliverability at {company}"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Email Body Copy</label>
                <textarea
                  rows={5}
                  required
                  placeholder="Paste high-converting email copy with placeholders like {name}, {company}, {topic}..."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-sans"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Style Notes / Guidance (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Peer-to-peer tone, sharp domain pain point, low-friction 10-min ask"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition"
                >
                  {submitting ? 'Saving...' : 'Add to Training Pool'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
