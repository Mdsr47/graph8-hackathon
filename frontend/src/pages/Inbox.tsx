import React, { useState } from 'react';
import {
  Mail,
  Sparkles,
  Send,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  RefreshCw,
  Plus,
  X,
  Clock,
  ArrowUpRight
} from 'lucide-react';
import { InboxItem } from '../types';

interface InboxProps {
  inboxItems: InboxItem[];
  onGenerateDraft: (id: string) => Promise<string>;
  onSendReply: (id: string, text: string) => Promise<void>;
  onNavigateApprovals: () => void;
  onSyncInbox?: () => Promise<void>;
  onComposeEmail?: (to: string, subject: string, body: string) => Promise<void>;
}

export const Inbox: React.FC<InboxProps> = ({
  inboxItems,
  onGenerateDraft,
  onSendReply,
  onNavigateApprovals,
  onSyncInbox,
  onComposeEmail,
}) => {
  const [selectedId, setSelectedId] = useState<string>(inboxItems[0]?.id || '');
  const [generating, setGenerating] = useState(false);
  const [draftText, setDraftText] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [sendingReply, setSendingReply] = useState(false);
  const [replySuccess, setReplySuccess] = useState(false);

  // Compose Modal State
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [sendingCompose, setSendingCompose] = useState(false);
  const [composeSuccess, setComposeSuccess] = useState<string | null>(null);

  const selectedItem = inboxItems.find((i) => i.id === selectedId) || inboxItems[0];

  const handleGenerate = async () => {
    if (!selectedItem) return;
    setGenerating(true);
    setReplySuccess(false);
    try {
      const draft = await onGenerateDraft(selectedItem.id);
      setDraftText(draft);
    } finally {
      setGenerating(false);
    }
  };

  const handleSendDirectReply = async () => {
    if (!selectedItem || !draftText) return;
    setSendingReply(true);
    setReplySuccess(false);
    try {
      await onSendReply(selectedItem.id, draftText);
      setReplySuccess(true);
      setTimeout(() => setReplySuccess(false), 4000);
    } catch (err: any) {
      alert(`Send failed: ${err.message || 'Error sending reply'}`);
    } finally {
      setSendingReply(false);
    }
  };

  const handleSync = async () => {
    if (!onSyncInbox) return;
    setSyncing(true);
    setSyncMessage(null);
    try {
      await onSyncInbox();
      setSyncMessage('IMAP Sync Complete');
      setTimeout(() => setSyncMessage(null), 3000);
    } catch (err: any) {
      setSyncMessage(`Sync failed: ${err.message || 'Error'}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleSendCompose = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onComposeEmail || !composeTo || !composeSubject || !composeBody) return;
    setSendingCompose(true);
    setComposeSuccess(null);
    try {
      await onComposeEmail(composeTo, composeSubject, composeBody);
      setComposeSuccess(`Delivered to ${composeTo} via SMTP!`);
      setTimeout(() => {
        setIsComposeOpen(false);
        setComposeTo('');
        setComposeSubject('');
        setComposeBody('');
        setComposeSuccess(null);
      }, 2000);
    } catch (err: any) {
      alert(`Failed to send: ${err.message || 'SMTP error'}`);
    } finally {
      setSendingCompose(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            AI Inbox & Outbound Messaging
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              Live SMTP & IMAP Mailbox
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real inbound prospect emails read via IMAP, classified with AI sentiment, and delivered via your SMTP.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {syncMessage && (
            <span className="text-xs text-emerald-400 font-semibold animate-pulse">
              {syncMessage}
            </span>
          )}

          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>{syncing ? 'Syncing IMAP...' : 'Sync Inbox (IMAP)'}</span>
          </button>

          <button
            onClick={() => setIsComposeOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Compose Email (SMTP)</span>
          </button>
        </div>
      </div>

      {/* Main Split View: Left List / Right Reading & Reply Pane */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left: Message List */}
        <div className="lg:col-span-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs font-bold text-slate-300">
            <span>Incoming Replies ({inboxItems.length})</span>
            <span className="text-[11px] text-slate-500 font-normal">Real-time sync</span>
          </div>

          <div className="divide-y divide-slate-800 overflow-y-auto flex-1">
            {inboxItems.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 space-y-2">
                <Mail className="w-8 h-8 text-slate-700 mx-auto" />
                <p className="font-semibold text-slate-400">No incoming messages yet</p>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                  Click <strong>"Sync Inbox (IMAP)"</strong> above to pull recent messages from your configured mailbox, or send a test email.
                </p>
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
                      setReplySuccess(false);
                    }}
                    className={`p-4 cursor-pointer transition space-y-1.5 ${
                      isSelected
                        ? 'bg-slate-800/80 border-l-4 border-indigo-500'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white truncate max-w-[200px]">{item.contact_name}</span>
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

                    <div className="text-[11px] text-indigo-400 font-medium truncate">{item.company || item.contact_email}</div>
                    <div className="text-xs text-slate-300 font-medium line-clamp-1">{item.subject}</div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{item.body}</p>
                    <div className="text-[10px] text-slate-500 pt-1 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3 text-slate-600" />
                      <span>{new Date(item.received_at).toLocaleString()}</span>
                    </div>
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
                    {new Date(selectedItem.received_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex flex-wrap items-center gap-2">
                  <span>From: <strong className="text-white">{selectedItem.contact_name}</strong> &lt;{selectedItem.contact_email}&gt;</span>
                  <span>•</span>
                  <span className="text-indigo-400 font-medium">{selectedItem.company}</span>
                </div>
              </div>

              {/* Message Body */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-wrap max-h-48 overflow-y-auto">
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
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{generating ? 'Formulating...' : 'Generate AI Draft'}</span>
                  </button>
                </div>

                <div className="flex-1 min-h-[120px]">
                  <textarea
                    rows={5}
                    placeholder="Click 'Generate AI Draft' to let Groq LLM formulate a tailored reply, or write custom response..."
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    className="w-full h-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                  />
                </div>

                {replySuccess && (
                  <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Reply delivered via SMTP successfully!</span>
                  </div>
                )}

                {/* Action Buttons Row */}
                <div className="flex items-center justify-between pt-1">
                  <div className="text-[11px] text-slate-500">
                    Draft will be queued in Approvals or can be sent directly via SMTP.
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={onNavigateApprovals}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                    >
                      Queue in Approvals
                    </button>

                    <button
                      disabled={sendingReply || !draftText}
                      onClick={handleSendDirectReply}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{sendingReply ? 'Sending SMTP...' : 'Send Reply via SMTP'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-slate-500 space-y-2">
              <Mail className="w-8 h-8 text-slate-700 mx-auto" />
              <p>Select an inbound message from the list to view and draft reply.</p>
            </div>
          )}
        </div>
      </div>

      {/* COMPOSE NEW EMAIL MODAL */}
      {isComposeOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
              <div className="flex items-center gap-2.5">
                <Send className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Compose New Outbound Email (SMTP)</h3>
              </div>
              <button onClick={() => setIsComposeOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSendCompose} className="p-5 space-y-4 text-xs">
              {composeSuccess && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{composeSuccess}</span>
                </div>
              )}

              <div>
                <label className="block text-slate-400 font-semibold mb-1">To Email Address:</label>
                <input
                  type="email"
                  required
                  placeholder="recipient@company.com"
                  value={composeTo}
                  onChange={(e) => setComposeTo(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Subject:</label>
                <input
                  type="text"
                  required
                  placeholder="Quick question regarding your revenue operations"
                  value={composeSubject}
                  onChange={(e) => setComposeSubject(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Body Text:</label>
                <textarea
                  rows={6}
                  required
                  placeholder="Hi there, write your outbound message here..."
                  value={composeBody}
                  onChange={(e) => setComposeBody(e.target.value)}
                  className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500 font-sans leading-relaxed"
                />
              </div>

              <div className="p-3 border-t border-slate-800 bg-slate-800/30 flex items-center justify-between -mx-5 -mb-5 px-5 py-3">
                <span className="text-[11px] text-slate-500">Delivered via your configured SMTP server</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsComposeOpen(false)}
                    className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={sendingCompose}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{sendingCompose ? 'Sending...' : 'Send Email'}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
