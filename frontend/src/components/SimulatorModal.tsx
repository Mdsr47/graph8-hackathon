import React, { useState } from 'react';
import { X, Send, Eye, MessageSquareText, CalendarCheck, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { Campaign } from '../types';

interface SimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaigns: Campaign[];
  onTriggerSimulate: (eventType: string, sentiment?: string, replyText?: string) => Promise<void>;
}

export const SimulatorModal: React.FC<SimulatorModalProps> = ({
  isOpen,
  onClose,
  campaigns,
  onTriggerSimulate,
}) => {
  const [selectedCampaign, setSelectedCampaign] = useState(campaigns[0]?.id || '');
  const [customReply, setCustomReply] = useState('Hi Alex, thanks for reaching out. Yes, we burned two secondary domains last month. How does your self-healing loop work? Can we see a demo Thursday 2pm EST?');
  const [loading, setLoading] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSimulate = async (eventType: string, sentiment?: string, text?: string) => {
    setLoading(true);
    setLastMessage(null);
    try {
      await onTriggerSimulate(eventType, sentiment, text);
      setLastMessage(`✅ Simulated ${eventType.toUpperCase()} event successfully dispatched to agent loop!`);
    } catch (e: any) {
      setLastMessage(`❌ Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/40">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              ⚡
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Live Webhook Simulator</h3>
              <p className="text-xs text-slate-400">Trigger simulated graph8 webhook telemetry for judging</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {lastMessage && (
            <div className="p-3 rounded-lg bg-slate-800 text-xs font-mono text-emerald-400 border border-emerald-500/30">
              {lastMessage}
            </div>
          )}

          {/* Quick 1-Click Scenarios */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              1-Click Telemetry Events
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                disabled={loading}
                onClick={() => handleSimulate('sent')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-left transition group"
              >
                <Send className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition" />
                <div>
                  <div className="text-xs font-bold text-white">Simulate 1 Send</div>
                  <div className="text-[11px] text-slate-400">Logs sequence step</div>
                </div>
              </button>

              <button
                disabled={loading}
                onClick={() => handleSimulate('opened')}
                className="flex items-center gap-2 p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-left transition group"
              >
                <Eye className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition" />
                <div>
                  <div className="text-xs font-bold text-white">Simulate Email Open</div>
                  <div className="text-[11px] text-slate-400">Updates variant metrics</div>
                </div>
              </button>

              <button
                disabled={loading}
                onClick={() => handleSimulate('replied', 'positive', customReply)}
                className="flex items-center gap-2 p-3 rounded-xl bg-emerald-950/40 hover:bg-emerald-900/40 border border-emerald-500/40 text-left transition group"
              >
                <MessageSquareText className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition" />
                <div>
                  <div className="text-xs font-bold text-emerald-300">🔥 Positive Reply</div>
                  <div className="text-[11px] text-slate-400">Demo request hook</div>
                </div>
              </button>

              <button
                disabled={loading}
                onClick={() => handleSimulate('meeting_booked')}
                className="flex items-center gap-2 p-3 rounded-xl bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/40 text-left transition group"
              >
                <CalendarCheck className="w-4 h-4 text-purple-400 group-hover:scale-110 transition" />
                <div>
                  <div className="text-xs font-bold text-purple-300">Meeting Booked</div>
                  <div className="text-[11px] text-slate-400">Ultimate conversion</div>
                </div>
              </button>
            </div>
          </div>

          {/* Simulate 5 Sends (Sample Size Threshold) */}
          <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="text-xs font-bold text-white">Trigger Self-Healing Loop</span>
                <p className="text-[11px] text-slate-400">Dispatches 5 sends + 1 positive reply on Variant B to trigger Kill & Reallocation</p>
              </div>
              <button
                disabled={loading}
                onClick={async () => {
                  setLoading(true);
                  try {
                    for (let i = 0; i < 5; i++) {
                      await onTriggerSimulate('sent');
                    }
                    await onTriggerSimulate('replied', 'positive', customReply);
                    setLastMessage("✅ Dispatched 5 sends + positive reply. Self-healing reinforcement evaluated!");
                  } finally {
                    setLoading(false);
                  }
                }}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition shrink-0"
              >
                Auto-Trigger Loop ⚡
              </button>
            </div>
          </div>

          {/* Custom Reply Box */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Custom Prospect Reply Text:
            </label>
            <textarea
              rows={3}
              value={customReply}
              onChange={(e) => setCustomReply(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
