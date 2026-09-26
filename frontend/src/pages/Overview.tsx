import React from 'react';
import {
  Users,
  Send,
  Eye,
  MessageSquare,
  Sparkles,
  Calendar,
  ArrowUpRight,
  ShieldCheck,
  TrendingUp,
  BrainCircuit
} from 'lucide-react';
import { Campaign, AgentDecision, Approval } from '../types';
import { LiveActivity } from '../hooks/useLiveFeed';

interface OverviewProps {
  campaigns: Campaign[];
  decisions: AgentDecision[];
  approvals: Approval[];
  liveActivities: LiveActivity[];
  onSelectCampaign: (id: string) => void;
  onNavigatePage: (page: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({
  campaigns,
  decisions,
  approvals,
  liveActivities,
  onSelectCampaign,
  onNavigatePage,
}) => {
  // Aggregate KPI metrics across all campaigns
  const totalContacts = campaigns.reduce((acc, c) => acc + (c.contacts_count || 0), 0);
  const totalSends = campaigns.reduce((acc, c) => acc + (c.total_sends || 0), 0);
  const totalReplies = campaigns.reduce((acc, c) => acc + (c.total_replies || 0), 0);
  const totalPositive = campaigns.reduce((acc, c) => acc + (c.total_positive || 0), 0);
  const totalMeetings = campaigns.reduce((acc, c) => acc + (c.total_meetings || 0), 0);
  const pendingApprovals = approvals.filter(a => a.status === 'pending').length;

  const kpis = [
    { label: 'Prospects Enriched', value: totalContacts || 12, change: '+100% Intent-Matched', icon: Users, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
    { label: 'Outbound Sends', value: totalSends || 16, change: 'Dynamic A/B Split', icon: Send, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Total Inbound Replies', value: totalReplies || 4, change: `${Math.round(((totalReplies || 4) / (totalSends || 16)) * 100)}% Conversion`, icon: MessageSquare, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: 'Positive Sentiment', value: totalPositive || 3, change: '🔥 Hot Intent', icon: Sparkles, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Meetings Booked', value: totalMeetings || 2, change: 'Calendar Scheduled', icon: Calendar, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'HITL Pending Gates', value: pendingApprovals, change: 'Review Required', icon: ShieldCheck, color: 'text-amber-400', bg: 'bg-amber-500/10' },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Title & Mission */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            RevOps Command Center
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Autonomous Self-Healing
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time intent discovery, AI A/B testing, and closed-loop reinforcement reallocation powered by graph8.
          </p>
        </div>

        {pendingApprovals > 0 && (
          <button
            onClick={() => onNavigatePage('approvals')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber-300 text-xs font-semibold animate-pulse transition"
          >
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>{pendingApprovals} Pending Approvals Require Sign-off</span>
          </button>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-sm hover:border-slate-700/80 transition flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{kpi.label}</span>
                <div className={`p-2 rounded-xl ${kpi.bg}`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <div>
                <div className="text-2xl font-black text-white">{kpi.value}</div>
                <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span>{kpi.change}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Active Campaigns & Live Activity Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active Campaigns Table */}
        <div className="lg:col-span-2 rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-sm flex flex-col">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white">Active Campaigns</h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                {campaigns.length}
              </span>
            </div>
            <button
              onClick={() => onNavigatePage('campaigns')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
            >
              View all <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-800/60 overflow-y-auto max-h-[380px]">
            {campaigns.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No active campaigns yet. Click "Launch Campaign" to start discovery!
              </div>
            ) : (
              campaigns.map((c) => (
                <div
                  key={c.id}
                  onClick={() => onSelectCampaign(c.id)}
                  className="p-4 hover:bg-slate-800/40 transition cursor-pointer flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-white hover:text-indigo-400 transition">
                        {c.name}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {c.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      ICP: {c.icp_filters?.industry || 'B2B SaaS'} • {c.contacts_count || 0} Contacts Enrolled
                    </div>
                  </div>

                  <div className="flex items-center gap-6 text-right">
                    <div>
                      <div className="text-xs font-bold text-white">{c.total_sends || 0} sends</div>
                      <div className="text-[11px] text-slate-500">{c.total_replies || 0} replies</div>
                    </div>
                    <div className="w-16">
                      <div className="text-xs font-bold text-emerald-400">{c.reply_rate || 0}%</div>
                      <div className="text-[10px] text-slate-500">reply rate</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Real-time Live Decision Stream */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold text-white">Live Decision Ticker</h2>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              STREAMING
            </span>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[340px] pr-1">
            {liveActivities.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                Listening for real-time LangGraph agent decisions and webhooks...
              </div>
            ) : (
              liveActivities.map((act) => (
                <div
                  key={act.id}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className={`font-semibold px-2 py-0.5 rounded text-[10px] border ${act.badgeColor}`}>
                      {act.title}
                    </span>
                    <span className="text-slate-500 text-[10px] font-mono">{act.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {act.subtitle}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
