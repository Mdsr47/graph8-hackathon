import React, { useState, useEffect } from 'react';
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
  RotateCcw,
  Server,
  Lock,
  Eye,
  EyeOff,
  AlertCircle
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

  // Mailbox Direct SMTP/IMAP state
  const [provider, setProvider] = useState<'gmail' | 'outlook' | 'custom'>('gmail');
  const [fromName, setFromName] = useState('RevOps Outbound Agent');
  const [fromEmail, setFromEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [smtpHost, setSmtpHost] = useState('smtp.gmail.com');
  const [smtpPort, setSmtpPort] = useState(587);
  const [imapHost, setImapHost] = useState('imap.gmail.com');
  const [imapPort, setImapPort] = useState(993);
  const [mailboxStatus, setMailboxStatus] = useState<string>('disconnected');
  const [lastSyncedAt, setLastSyncedAt] = useState<string>('');
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [savingConfig, setSavingConfig] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    fetch('/api/mailboxes/settings')
      .then(res => res.json())
      .then(data => {
        if (data) {
          setProvider(data.provider || 'gmail');
          setFromName(data.from_name || 'RevOps Outbound Agent');
          setFromEmail(data.from_email || data.smtp_username || '');
          setSmtpHost(data.smtp_host || 'smtp.gmail.com');
          setSmtpPort(data.smtp_port || 587);
          setImapHost(data.imap_host || 'imap.gmail.com');
          setImapPort(data.imap_port || 993);
          setMailboxStatus(data.status || 'disconnected');
          setLastSyncedAt(data.last_synced_at || '');
        }
      })
      .catch(err => console.error('Failed to load mailbox settings:', err));
  }, []);

  const handleProviderSelect = (p: 'gmail' | 'outlook' | 'custom') => {
    setProvider(p);
    setTestResult(null);
    if (p === 'gmail') {
      setSmtpHost('smtp.gmail.com');
      setSmtpPort(587);
      setImapHost('imap.gmail.com');
      setImapPort(993);
    } else if (p === 'outlook') {
      setSmtpHost('smtp.office365.com');
      setSmtpPort(587);
      setImapHost('outlook.office365.com');
      setImapPort(993);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/mailboxes/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          from_name: fromName,
          from_email: fromEmail,
          smtp_host: smtpHost,
          smtp_port: smtpPort,
          smtp_username: fromEmail,
          smtp_password: password,
          imap_host: imapHost,
          imap_port: imapPort,
          imap_username: fromEmail,
          imap_password: password,
        })
      });
      const data = await res.json();
      setTestResult(data);
    } catch (err: any) {
      setTestResult({ success: false, error: err.message || 'Connection test failed' });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSaveMailbox = async () => {
    setSavingConfig(true);
    setSaveSuccess(false);
    try {
      const res = await fetch('/api/mailboxes/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          from_name: fromName,
          from_email: fromEmail,
          smtp_host: smtpHost,
          smtp_port: smtpPort,
          smtp_username: fromEmail,
          smtp_password: password,
          imap_host: imapHost,
          imap_port: imapPort,
          imap_username: fromEmail,
          imap_password: password,
        })
      });
      if (res.ok) {
        setSaveSuccess(true);
        setMailboxStatus('connected');
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error('Failed to save mailbox settings:', err);
    } finally {
      setSavingConfig(false);
    }
  };

  const copyWebhook = () => {
    navigator.clipboard.writeText(settings.webhook_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isConnected = mailboxStatus === 'connected' || settings.mailbox?.status === 'active';

  return (
    <div className="p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight">System Settings & Connections</h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure direct SMTP/IMAP credentials for live email sending and receiving, API integrations, and autonomous parameters.
        </p>
      </div>

      {/* DIRECT SMTP & IMAP MAILBOX CONFIGURATION CARD */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Sending & Inbound Mailbox Configuration (SMTP & IMAP)
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Direct Integration
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Configure your email provider to send outbound pitches and read real inbound prospect replies.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold ${
              isConnected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span>{isConnected ? `Connected ✅ (${fromEmail || 'Active'})` : 'Not Connected'}</span>
            </span>
          </div>
        </div>

        {/* Provider Presets */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-400">Select Provider Preset:</label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'gmail', label: 'Google / Gmail', desc: 'smtp.gmail.com:587' },
              { id: 'outlook', label: 'Microsoft / Outlook', desc: 'smtp.office365.com:587' },
              { id: 'custom', label: 'Custom SMTP & IMAP', desc: 'Manual server configuration' },
            ].map(p => (
              <button
                key={p.id}
                type="button"
                onClick={() => handleProviderSelect(p.id as any)}
                className={`p-3 rounded-xl border text-left transition ${
                  provider === p.id
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold text-white">{p.label}</div>
                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Form Inputs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-400 font-semibold mb-1">Display / Sender Name:</label>
            <input
              type="text"
              value={fromName}
              onChange={e => setFromName(e.target.value)}
              placeholder="e.g. Alex Hayes"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Sender Email Address (Username):</label>
            <input
              type="email"
              value={fromEmail}
              onChange={e => setFromEmail(e.target.value)}
              placeholder="youremail@gmail.com"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="md:col-span-2">
            <div className="flex items-center justify-between mb-1">
              <label className="text-slate-400 font-semibold">Password or App Password:</label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-[11px] text-indigo-400 hover:underline flex items-center gap-1"
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                <span>{showPassword ? 'Hide' : 'Show'}</span>
              </button>
            </div>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={provider === 'gmail' ? '16-character Google App Password (e.g. abcd efgh ijkl mnop)' : 'Your email password'}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
            {provider === 'gmail' && (
              <p className="text-[11px] text-slate-500 mt-1">
                💡 <span className="text-slate-400 font-medium">Gmail Tip:</span> Use a 16-character App Password from{' '}
                <a
                  href="https://myaccount.google.com/apppasswords"
                  target="_blank"
                  rel="noreferrer"
                  className="text-indigo-400 hover:underline"
                >
                  myaccount.google.com/apppasswords
                </a>.
              </p>
            )}
          </div>

          {/* Server Details */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider block">Outbound SMTP Server</span>
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2">
                <label className="text-[10px] text-slate-500 block mb-0.5">Host:</label>
                <input
                  type="text"
                  value={smtpHost}
                  onChange={e => setSmtpHost(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 block mb-0.5">Port:</label>
                <input
                  type="number"
                  value={smtpPort}
                  onChange={e => setSmtpPort(Number(e.target.value))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-[11px]"
                />
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider block">Inbound IMAP Server</span>
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2">
                <label className="text-[10px] text-slate-500 block mb-0.5">Host:</label>
                <input
                  type="text"
                  value={imapHost}
                  onChange={e => setImapHost(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 block mb-0.5">Port:</label>
                <input
                  type="number"
                  value={imapPort}
                  onChange={e => setImapPort(Number(e.target.value))}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-[11px]"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Live Test Feedback Banner */}
        {testResult && (
          <div className={`p-3.5 rounded-xl border text-xs space-y-1 ${
            testResult.success
              ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
          }`}>
            <div className="font-bold flex items-center gap-1.5">
              {testResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
              <span>{testResult.success ? 'Connection Test Passed!' : 'Connection Test Failed'}</span>
            </div>
            {testResult.imap && <div className="text-[11px]">{testResult.imap.message}</div>}
            {testResult.smtp && <div className="text-[11px]">{testResult.smtp.message}</div>}
            {testResult.error && <div className="text-[11px]">{testResult.error}</div>}
          </div>
        )}

        {/* Buttons Row */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-[11px] text-slate-500">
            {lastSyncedAt ? `Last IMAP sync: ${new Date(lastSyncedAt).toLocaleTimeString()}` : 'Not synced yet'}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={testingConnection || !fromEmail}
              onClick={handleTestConnection}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition disabled:opacity-50"
            >
              {testingConnection ? 'Testing Connection...' : '⚡ Test Connection'}
            </button>

            <button
              type="button"
              disabled={savingConfig || !fromEmail}
              onClick={handleSaveMailbox}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {savingConfig ? 'Saving...' : saveSuccess ? 'Saved & Connected ✅' : 'Save Mailbox Credentials'}
            </button>
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
