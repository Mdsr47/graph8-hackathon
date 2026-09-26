import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Flame,
  Skull,
  CheckCircle2,
  Send,
  Eye,
  MessageSquare,
  Sparkles,
  BrainCircuit,
  Users
} from 'lucide-react';
import { Campaign, Variant, Contact, AgentDecision } from '../types';

interface CampaignDetailProps {
  campaignId: string;
  onBack: () => void;
}

export const CampaignDetail: React.FC<CampaignDetailProps> = ({ campaignId, onBack }) => {
  const [data, setData] = useState<{
    campaign: Campaign;
    variants: Variant[];
    contacts: Contact[];
    decisions: AgentDecision[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDetail = async () => {
    try {
      const res = await fetch(`/api/campaigns/${campaignId}`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error('Failed to fetch campaign detail:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    const interval = setInterval(fetchDetail, 4000);
    return () => clearInterval(interval);
  }, [campaignId]);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Loading campaign intelligence telemetry...
      </div>
    );
  }

  const { campaign, variants, contacts, decisions } = data;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Overview</span>
        </button>

        <span className="text-xs font-bold px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
          Campaign ID: {campaign.id.slice(0, 8)}...
        </span>
      </div>

      {/* Header Info */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-white">{campaign.name}</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
              {campaign.status}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            ICP: {campaign.icp_filters?.industry || 'B2B SaaS'} • Keywords: {campaign.icp_filters?.keywords?.join(', ') || 'N/A'}
          </p>
        </div>

        {/* Live Reinforcement Status */}
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5">
              <BrainCircuit className="w-4 h-4 text-indigo-400" />
              <span>Reinforcement Scoring</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Bayesian confidence smoothing active (<strong className="text-white">Min 5 sends</strong>)
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Send className="w-4 h-4 text-emerald-400" />
              <span>Daily Send Pacing</span>
            </div>
            <div className="text-[11px] text-emerald-400 font-bold mt-0.5">
              {campaign.sent_today || 0} / {campaign.daily_limit || 50} Contacts Sent
            </div>
          </div>
        </div>
      </div>

      {/* A/B/n Pitch Variants Performance Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>A/B Copy Variants & Telemetry</span>
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {variants.filter(v => v.status === 'active').length} Active / {variants.filter(v => v.status === 'killed').length} Killed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {variants.map((v, i) => {
            const sends = v.sends_count || 0;
            const opens = v.opens_count || 0;
            const replies = v.replies_count || 0;
            const pos = v.positive_replies_count || 0;
            const isKilled = v.status === 'killed';
            const score = typeof v.score === 'number' ? v.score : 0.0;
            const alloc = typeof v.allocation_percentage === 'number' ? v.allocation_percentage : 50.0;

            return (
              <div
                key={v.id}
                className={`rounded-2xl border p-5 transition flex flex-col justify-between ${
                  isKilled
                    ? 'bg-slate-950/40 border-rose-900/40 opacity-70'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 shadow-sm'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                      Variant {String.fromCharCode(65 + i)}
                      {isKilled ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
                          <Skull className="w-3 h-3" /> KILLED BY AGENT
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> ACTIVE ({alloc}% Traffic)
                        </span>
                      )}
                    </span>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      Score: {score.toFixed(3)}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-medium text-white mb-3">
                    <span className="text-[11px] text-slate-400 block mb-0.5">Subject:</span>
                    {v.subject}
                  </div>

                  <p className="text-xs text-slate-400 whitespace-pre-line line-clamp-3 leading-relaxed mb-4">
                    {v.body_template}
                  </p>
                </div>

                {/* Performance Metrics */}
                <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-800/80 text-center">
                  <div className="p-2 rounded-lg bg-slate-950/60">
                    <div className="text-xs font-bold text-white">{sends}</div>
                    <div className="text-[10px] text-slate-500">Sends</div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-950/60">
                    <div className="text-xs font-bold text-cyan-400">{opens}</div>
                    <div className="text-[10px] text-slate-500">Opens</div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-950/60">
                    <div className="text-xs font-bold text-white">{replies}</div>
                    <div className="text-[10px] text-slate-500">Replies</div>
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-950/30 border border-emerald-500/20">
                    <div className="text-xs font-bold text-emerald-400">{pos} 🔥</div>
                    <div className="text-[10px] text-slate-400">Positive</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Grid: Enrolled Contacts & Campaign Decisions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enrolled Contacts */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-400" />
              <span>Enrolled Decision Makers ({contacts.length})</span>
            </h3>
          </div>

          <div className="space-y-2.5 max-h-[280px] overflow-y-auto">
            {contacts.map((c) => (
              <div key={c.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-white">{c.name}</div>
                  <div className="text-[11px] text-slate-400">{c.title} • {c.company}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-indigo-400">{c.intent_score} Intent</div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">
                    {c.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Campaign Decisions Audit Trail */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-purple-400" />
              <span>Agent Reinforcement Log</span>
            </h3>
          </div>

          <div className="space-y-2.5 max-h-[280px] overflow-y-auto">
            {decisions.map((d) => (
              <div key={d.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-300">
                    {d.decision_type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(d.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {d.reasoning}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
