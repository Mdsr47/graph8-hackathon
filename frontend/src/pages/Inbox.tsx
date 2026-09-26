import React, { useState } from 'react';
import { Mail, Sparkles, Send, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';
import { InboxItem } from '../types';

interface InboxProps {
  inboxItems: InboxItem[];
  onGenerateDraft: (id: string) => Promise<string>;
  onSendReply: (id: string, text: string) => Promise<void>;
  onNavigateApprovals: () => void;
}

export const Inbox: React.FC<InboxProps> = ({
  inboxItems,
  onGenerateDraft,
  onSendReply,
  onNavigateApprovals,
}) => {
  const [selectedId, setSelectedId] = useState<string>(inboxItems[0]?.id || '');
  const [generating, setGenerating] = useState(false);
  const [draftText, setDraftText] = useState('');
  const [sentSuccess, setSentSuccess] = useState(false);

  const selectedItem = inboxItems.find((i) => i.id === selectedId) || inboxItems[0];

  const handleGenerate = async () => {
    if (!selectedItem) return;
    setGenerating(true);
    setSentSuccess(false);
    try {
      const draft = await onGenerateDraft(selectedItem.id);
      setDraftText(draft);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            AI Inbox & Replies
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              Live Ingested via graph8 Native Mailbox
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time prospect replies classified with LLM sentiment analysis and supervised AI draft generator.
          </p>
        </div>
      </div>

      {/* Main Split View: Left List / Right Reading & Reply Pane */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left: Message List */}
        <div className="lg:col-span-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-950/40 text-xs font-bold text-slate-300">
            Incoming Replies ({inboxItems.length})
          </div>

          <div className="divide-y divide-slate-800 overflow-y-auto flex-1">
            {inboxItems.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No replies yet. Inbound emails from connected mailboxes will stream here automatically.
              </div>
            ) : (
              inboxItems.map((item) => {
                const isSelected = item.id === selectedItem?.id;
                const isPos = item.sentiment === 'positive';
                const isNeg = item.sentiment === 'negative';

                return (
                  <div
                    key={item.id}
                    onClick={() => {
                      setSelectedId(item.id);
                      setDraftText(item.ai_draft_reply || '');
                      setSentSuccess(false);
                    }}
                    className={`p-4 cursor-pointer transition space-y-1.5 ${
                      isSelected
                        ? 'bg-slate-800/80 border-l-4 border-indigo-500'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{item.contact_name}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          isPos
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : isNeg
                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                            : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                        }`}
                      >
                        {item.sentiment === 'positive' ? '🔥 Positive' : item.sentiment}
                      </span>
                    </div>

                    <div className="text-[11px] text-indigo-400 font-medium">{item.company}</div>
                    <div className="text-xs text-slate-300 font-medium line-clamp-1">{item.subject}</div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{item.body}</p>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Message Detail & AI Reply Assistant */}
        <div className="lg:col-span-7 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col overflow-hidden">
          {selectedItem ? (
            <div className="p-6 flex flex-col h-full space-y-5 overflow-y-auto">
              {/* Message Header */}
              <div className="pb-4 border-b border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold text-white">{selectedItem.subject}</h2>
                  <span className="text-xs font-mono text-slate-500">
                    {new Date(selectedItem.received_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <span>From: <strong className="text-white">{selectedItem.contact_name}</strong> &lt;{selectedItem.contact_email}&gt;</span>
                  <span>•</span>
                  <span className="text-indigo-400 font-medium">{selectedItem.company}</span>
                </div>
              </div>

              {/* Message Body */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans">
                {selectedItem.body}
              </div>

              {/* AI Reply Copilot Card */}
              <div className="flex-1 flex flex-col rounded-xl bg-slate-950/80 border border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-bold text-white">AI Contextual Reply Copilot</span>
                  </div>

                  <button
                    disabled={generating}
                    onClick={handleGenerate}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{generating ? 'Formulating...' : 'Generate AI Draft'}</span>
                  </button>
                </div>

                <div className="flex-1">
                  <textarea
                    rows={6}
                    placeholder="Click 'Generate AI Draft' to let LLM formulate a response proposing demo times..."
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    className="w-full h-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                  />
                </div>

                {/* HITL Gate Notice */}
                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    Section 9 Governance: AI replies are queued in Approvals before dispatch.
                  </span>
                  <button
                    onClick={onNavigateApprovals}
                    className="underline hover:text-white font-semibold"
                  >
                    Open Approvals Tab
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-slate-500">
              Select an inbound message to view and draft reply.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
