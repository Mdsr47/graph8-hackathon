import React, { useState } from 'react';
import {
  Mail,
  ExternalLink,
  Key,
  Cpu,
  Webhook,
  PhoneCall,
  CheckCircle2,
  Copy,
  Check,
  ShieldCheck,
  Zap,
  Trash2,
  RotateCcw
} from 'lucide-react';
import { SettingsData } from '../types';

interface SettingsProps {
  settings: SettingsData;
  onRefreshMailbox: () => Promise<void>;
  onResetDatabase?: () => Promise<void>;
}

export const Settings: React.FC<SettingsProps> = ({ settings, onRefreshMailbox, onResetDatabase }) => {
  const [copied, setCopied] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(settings.voice_escalation?.enabled || false);
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const copyWebhook = () => {
    navigator.clipboard.writeText(settings.webhook_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isMailboxConnected = settings.mailbox?.status === 'active' || settings.mailbox?.status === 'warming_up';

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">System Settings & Connections</h1>
        <p className="text-xs text-slate-400 mt-1">
          Review integrations, native mailbox connection status, and autonomous threshold configurations.
        </p>
      </div>

      {/* SECTION 6C: NATIVE MAILBOX CONNECTOR CARD */}
      <div className="rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/30 p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  Native graph8 Mailbox Connector (Gmail / Outlook)
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Section 6c Architecture
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Connect your sending inbox securely via OAuth inside graph8. We never store or handle raw email passwords.
                </p>
              </div>
            </div>

            {/* Live Connection Status Banner */}
            <div className="pt-2 flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold ${
                isMailboxConnected
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isMailboxConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                <span>
                  {isMailboxConnected
                    ? `Connected ✅ (${settings.mailbox?.provider?.toUpperCase()} — ${settings.mailbox?.email || 'Active Sending Inbox'})`
                    : 'Not Connected'}
                </span>
              </div>

              {settings.mailbox?.warmup_enabled && (
                <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  Warmup Active ({settings.mailbox.sent_today || 12}/{settings.mailbox.daily_limit || 50} sent today)
                </span>
              )}
            </div>
          </div>

          {/* Action Link out to graph8 Settings -> Mailboxes */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0">
            <button
              onClick={onRefreshMailbox}
              className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
            >
              Refresh Status
            </button>

            <a
              href={settings.graph8_mailbox_settings_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition"
            >
              <span>Open graph8 Mailbox Settings</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>

      {/* Grid of Other Configuration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* graph8 API Integration */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800">
            <Key className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">graph8 API Configuration</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">API Key Status:</span>
              <span className="font-mono text-white bg-slate-950 px-2 py-1 rounded border border-slate-800">
                {settings.graph8_api_key_status}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Base API URL:</span>
              <span className="font-mono text-slate-300 text-[11px] truncate max-w-[200px]">
                {settings.graph8_base_url}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Simulation / Sandbox Mode:</span>
              <span className="text-emerald-400 font-semibold">
                {settings.simulation_mode ? 'Enabled (Offline Demo Mode Active)' : 'Live API Mode'}
              </span>
            </div>
          </div>
        </div>

        {/* LLM Provider Configuration */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800">
            <Cpu className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">LLM Provider (Groq / OpenAI-compatible)</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Provider Interface:</span>
              <span className="font-semibold text-white">{settings.llm_provider}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">Model:</span>
              <span className="font-mono text-indigo-300 bg-slate-950 px-2 py-1 rounded border border-slate-800 text-[11px]">
                {settings.llm_model}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-400">API Key:</span>
              <span className="font-mono text-slate-300 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                {settings.llm_api_key_status}
              </span>
            </div>
          </div>
        </div>

        {/* Webhook Endpoint Display */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800">
            <Webhook className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Public Webhook Receiver Endpoint</h3>
          </div>

          <div className="space-y-2 text-xs">
            <p className="text-slate-400 text-[11px]">
              Register this URL under graph8 Settings → Webhooks to receive real-time opens, replies, and sends.
            </p>

            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="font-mono text-[11px] text-cyan-300 flex-1 truncate select-all">
                {settings.webhook_url}
              </span>
              <button
                onClick={copyWebhook}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition shrink-0"
                title="Copy webhook URL"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Stretch Goal: Voice Escalation Toggle */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <PhoneCall className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Voice Escalation (Stretch Goal)</h3>
            </div>
            <input
              type="checkbox"
              checked={voiceEnabled}
              onChange={(e) => setVoiceEnabled(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 focus:ring-0 cursor-pointer"
            />
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] font-bold text-amber-400 block mb-1">
                Official Scoping Status:
              </span>
              <p className="text-[11px] text-slate-300">
                {settings.voice_escalation?.badge || 'Voice escalation: logic complete — awaiting connected number.'}
              </p>
            </div>
            <p className="text-[11px] text-slate-500">
              When intent score exceeds 90, the agent queues a voice escalation approval gate.
            </p>
          </div>
        </div>

        {/* Database Management / Reset Zone */}
        <div className="rounded-2xl bg-rose-950/20 border border-rose-500/30 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-rose-500/20">
            <div className="flex items-center gap-2.5">
              <Trash2 className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-bold text-white">Database Management (Wipe & Refresh)</h3>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
              Fresh Test Mode
            </span>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs">
            <p className="text-[11px] text-slate-300 max-w-lg leading-relaxed">
              Wipe all past campaigns, discovered prospects, variants, events, decisions, and approvals to start a fresh test session. Default reference email templates will be preserved.
            </p>
            <button
              onClick={async () => {
                if (!window.confirm("Are you sure you want to clear all database records?")) return;
                setResetting(true);
                setResetSuccess(false);
                try {
                  if (onResetDatabase) {
                    await onResetDatabase();
                  } else {
                    await fetch('/api/settings/reset-database', { method: 'POST' });
                  }
                  setResetSuccess(true);
                  setTimeout(() => setResetSuccess(false), 5000);
                } finally {
                  setResetting(false);
                }
              }}
              disabled={resetting}
              className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition shadow-lg shadow-rose-900/40 shrink-0 flex items-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
              {resetting ? 'Resetting...' : 'Reset & Refresh Database'}
            </button>
          </div>
          {resetSuccess && (
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Database wiped cleanly! All dashboard screens have been refreshed to zero records.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
