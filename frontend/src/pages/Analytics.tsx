import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Mail,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Flame,
  Calendar,
  Sparkles,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Award,
  Zap,
  Percent
} from 'lucide-react';
import { AnalyticsData, VariantAnalyticsItem } from '../types';

export const Analytics: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedVariantId, setExpandedVariantId] = useState<string | null>(null);
  const [evaluatingCycle, setEvaluatingCycle] = useState<boolean>(false);
  const [cycleToast, setCycleToast] = useState<string | null>(null);

  const handleEvaluateCycle = async () => {
    const campId = selectedCampaignId !== 'all' ? selectedCampaignId : (analyticsData?.campaigns[0]?.id || null);
    if (!campId) {
      alert("Please select a specific campaign to evaluate its 15-day cycle milestone.");
      return;
    }
    setEvaluatingCycle(true);
    try {
      const res = await fetch(`/api/campaigns/${campId}/evaluate-cycle-milestone`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setCycleToast(`🎉 15-Day Milestone Evaluated! Champion scaled to 80% traffic and evolved ${data.challenger.label} for Cycle ${data.new_cycle}.`);
        await fetchAnalytics(selectedCampaignId);
      } else {
        alert(data.message || 'Milestone evaluation not ready.');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEvaluatingCycle(false);
      setTimeout(() => setCycleToast(null), 8000);
    }
  };

  const fetchAnalytics = async (campId: string) => {
    setLoading(true);
    try {
      const url = campId === 'all' ? '/api/analytics' : `/api/analytics?campaign_id=${campId}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setAnalyticsData(data);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(selectedCampaignId);
  }, [selectedCampaignId]);

  const summary = analyticsData?.summary || {
    total_sends: 0,
    total_delivered: 0,
    delivery_rate: 100,
    total_opens: 0,
    open_rate: 0,
    total_clicks: 0,
    click_rate: 0,
    total_replies: 0,
    reply_rate: 0,
    total_positive: 0,
    positive_reply_rate: 0,
    total_bounces: 0,
    bounce_rate: 0,
    total_meetings: 0,
    total_prospects: 0,
    total_variants: 0,
  };

  const variants = analyticsData?.variants || [];
  const campaigns = analyticsData?.campaigns || [];
  const intentDist = analyticsData?.intent_distribution || { tier_1_hot: 0, tier_2_warm: 0, tier_3_mild: 0 };

  const getVariantStatusBadge = (v: VariantAnalyticsItem) => {
    if (v.status === 'killed') {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1">
          <XCircle className="w-3 h-3" />
          KILLED (Self-Healed)
        </span>
      );
    }
    if (v.allocation_percentage >= 80) {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
          <Award className="w-3 h-3 text-emerald-400" />
          CHAMPION ({v.allocation_percentage}% Traffic)
        </span>
      );
    }
    return (
      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3 text-indigo-400" />
        ACTIVE ({v.allocation_percentage}% Traffic)
      </span>
    );
  };

  return (
    <div className="p-8 space-y-7 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            Variant Performance & Telemetry Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry breakdown across A/B pitch variants, open/reply benchmarks, deliverability, and reinforcement weights.
          </p>
        </div>

        {/* Campaign Selector & Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <select
            value={selectedCampaignId}
            onChange={(e) => setSelectedCampaignId(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Campaigns ({campaigns.length})</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => fetchAnalytics(selectedCampaignId)}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition"
            title="Refresh Analytics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Cycle Toast */}
      {cycleToast && (
        <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm flex items-center justify-between animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400 shrink-0" />
            <span>{cycleToast}</span>
          </div>
          <button onClick={() => setCycleToast(null)} className="text-slate-400 hover:text-white text-xs ml-4">✕</button>
        </div>
      )}

      {/* 15-Day Self-Healing Reinforcement Cycle Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2.5">
            <span className="text-[11px] font-black uppercase px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 tracking-wider">
              {analyticsData?.cycle_info?.phase || "Cycle 1: Exploration Phase (50/50 Split)"}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              Day {analyticsData?.cycle_info?.current_day || 1} of {analyticsData?.cycle_info?.max_days || 15}
            </span>
          </div>
          <p className="text-xs text-slate-300">
            {analyticsData?.cycle_info?.cycle_number === 1 ? (
              "Initial 15-day exploration tournament. Outbound volume is split 50/50 between variants to establish statistically sound Bayesian baselines before scaling the winner."
            ) : (
              `Cycle ${analyticsData?.cycle_info?.cycle_number || 2}: Champion variant scaled to 80% traffic allocation while Evolutionary Challenger competes on remaining 20% traffic.`
            )}
          </p>

          {/* Progress Bar for 15 Days */}
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden max-w-md">
            <div
              className="bg-indigo-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, (((analyticsData?.cycle_info?.current_day || 1) / (analyticsData?.cycle_info?.max_days || 15)) * 100))}%` }}
            />
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
          <button
            onClick={handleEvaluateCycle}
            disabled={evaluatingCycle || !variants.length}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 cursor-pointer"
            title="Fast-forward: Evaluates DB performance metrics, crowns Champion to 80% traffic, and breeds Variant C via LLM"
          >
            <Zap className={`w-3.5 h-3.5 text-amber-300 ${evaluatingCycle ? 'animate-spin' : ''}`} />
            {evaluatingCycle ? "Evaluating Milestone..." : "⚡ Evaluate 15-Day Milestone Now"}
          </button>
        </div>
      </div>

      {/* Outbound & Telemetry Clarity Notice */}
      <div className="px-4 py-2.5 rounded-xl bg-slate-900/50 border border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-indigo-400 font-bold">● Telemetry Notice:</span>
          <span>
            Outbound numbers reflect prospects dispatched to Graph8 sequences following daily batch pacing. Inbound opens, clicks, and sentiment stream in real-time via webhook events.
          </span>
        </div>
        <span className="text-[10px] text-slate-500 hidden sm:inline">Bayesian Laplace Smoothing (k=3.0)</span>
      </div>

      {/* Top KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* Outbound Sends */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Outbound Sent</span>
            <Send className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">{summary.total_sends}</div>
          <div className="text-[10px] text-slate-400 truncate">
            {summary.total_delivered} delivered
          </div>
        </div>

        {/* Deliverability Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Deliverability</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">{summary.delivery_rate}%</div>
          <div className="text-[10px] text-slate-400 truncate">
            {summary.total_bounces} bounces
          </div>
        </div>

        {/* Unique Open Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Open Rate</span>
            <Mail className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-2xl font-black text-sky-400 font-mono">{summary.open_rate}%</div>
          <div className="text-[10px] text-slate-400 truncate">
            {summary.total_opens} opens
          </div>
        </div>

        {/* Reply Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Reply Rate</span>
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-400 font-mono">{summary.reply_rate}%</div>
          <div className="text-[10px] text-slate-400 truncate">
            {summary.total_replies} replies
          </div>
        </div>

        {/* Positive Sentiment Rate */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Positive 🔥</span>
            <Flame className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono">{summary.positive_reply_rate}%</div>
          <div className="text-[10px] text-slate-400 truncate">
            {summary.total_positive} hot replies
          </div>
        </div>

        {/* Meetings / Demos */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-[10px] uppercase font-bold tracking-wider">Meetings</span>
            <Calendar className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-purple-400 font-mono">{summary.total_meetings}</div>
          <div className="text-[10px] text-slate-400 truncate">
            Booked calls
          </div>
        </div>
      </div>

      {/* A/B Variant Detailed Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">A/B Testing Variants Performance</h2>
            <p className="text-xs text-slate-400">Comparing subject angles, hook conversions, dynamic reinforcement scores, and email copy.</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{variants.length} Variants Deployed</span>
        </div>

        {variants.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 rounded-2xl bg-slate-900 border border-slate-800">
            <Sparkles className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="font-semibold text-slate-300">No active variants found</p>
            <p className="mt-1">Launch a campaign to generate initial A/B pitch variants and track telemetry.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {variants.map((v, idx) => {
              const isExpanded = expandedVariantId === v.variant_id;
              const angleLabel = idx === 0 ? 'Variant A (Pain Point Hook)' : idx === 1 ? 'Variant B (ROI & Metrics Benchmark)' : `Variant ${String.fromCharCode(65 + idx)} (Evolved Mutant)`;
              const accentColor = idx === 0 ? 'indigo' : idx === 1 ? 'purple' : 'emerald';

              return (
                <div
                  key={v.variant_id}
                  className={`rounded-2xl bg-slate-900/80 border p-5 shadow-sm transition space-y-4 ${
                    v.status === 'killed'
                      ? 'border-rose-900/40 opacity-75'
                      : idx === 0
                      ? 'border-indigo-500/30'
                      : 'border-purple-500/30'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-bold uppercase tracking-wider text-${accentColor}-300`}>
                          {angleLabel}
                        </span>
                        {getVariantStatusBadge(v)}
                      </div>
                      <h3 className="text-sm font-bold text-white leading-snug">
                        "{v.subject}"
                      </h3>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Campaign: <span className="text-slate-300">{v.campaign_name}</span> &bull; <span className="font-mono text-[10px]">ID: {v.variant_id.slice(0, 8)}</span>
                      </div>
                    </div>

                    {/* AI Score Badge */}
                    <div className="text-right shrink-0">
                      <div className="text-[10px] text-slate-400 uppercase font-bold">AI Score</div>
                      <div className={`text-sm font-black font-mono ${v.score >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {v.score > 0 ? `+${v.score.toFixed(2)}` : v.score.toFixed(2)}
                      </div>
                    </div>
                  </div>

                  {/* Comparative Metric Bars */}
                  <div className="space-y-2.5 pt-2 border-t border-slate-800 text-xs">
                    {/* Open Rate Bar */}
                    <div>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-400">Open Rate:</span>
                        <span className="font-bold text-sky-400 font-mono">{v.metrics.openRate}% ({v.metrics.opens}/{v.metrics.sent})</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-sky-500 rounded-full transition-all"
                          style={{ width: `${Math.min(v.metrics.openRate, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Reply Rate Bar */}
                    <div>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-400">Reply Rate:</span>
                        <span className="font-bold text-cyan-400 font-mono">{v.metrics.replyRate}% ({v.metrics.replies}/{v.metrics.sent})</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-cyan-500 rounded-full transition-all"
                          style={{ width: `${Math.min(v.metrics.replyRate * 3, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Positive Reply Rate Bar */}
                    <div>
                      <div className="flex justify-between text-[11px] mb-1">
                        <span className="text-slate-400">Positive Reply Rate:</span>
                        <span className="font-bold text-amber-400 font-mono">{v.metrics.positiveReplyRate}% ({v.metrics.positiveReplies}/{v.metrics.sent})</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full transition-all"
                          style={{ width: `${Math.min(v.metrics.positiveReplyRate * 5, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Detailed Metric Pills */}
                  <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-800/80 text-center">
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Sent</div>
                      <div className="text-xs font-bold text-white font-mono">{v.metrics.sent}</div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Delivered</div>
                      <div className="text-xs font-bold text-emerald-400 font-mono">{v.metrics.delivered}</div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Bounces</div>
                      <div className="text-xs font-bold text-rose-400 font-mono">{v.metrics.bounces}</div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Traffic</div>
                      <div className="text-xs font-bold text-indigo-300 font-mono">{v.allocation_percentage}%</div>
                    </div>
                  </div>

                  {/* Expandable Email Copy Preview */}
                  <div className="pt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => setExpandedVariantId(isExpanded ? null : v.variant_id)}
                      className="w-full flex items-center justify-between text-xs text-indigo-400 hover:text-indigo-300 transition py-1"
                    >
                      <span className="font-semibold">{isExpanded ? 'Hide Email Body' : 'Inspect Full Email Body'}</span>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    {isExpanded && (
                      <div className="mt-2.5 p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-wrap animate-in fade-in duration-150">
                        {v.body_template}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ICP Intent Score Cohort Breakdown */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <Zap className="w-4 h-4 text-indigo-400" />
              ICP Buying Intent Velocity Distribution
            </h3>
            <p className="text-xs text-slate-400">Prospect intent tiers discovered and stored in database.</p>
          </div>
          <span className="text-xs font-mono text-slate-400">{summary.total_prospects} Total Prospect Records</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-500/30 space-y-1">
            <span className="text-[10px] uppercase font-bold text-emerald-400">Tier 1: High Velocity (90-100)</span>
            <div className="text-2xl font-black text-white font-mono">{intentDist.tier_1_hot} Prospects</div>
            <p className="text-[11px] text-slate-400">Active competitor search, pricing page visits, highest meeting conversion rate.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-indigo-500/30 space-y-1">
            <span className="text-[10px] uppercase font-bold text-indigo-300">Tier 2: Warm Intent (80-89)</span>
            <div className="text-2xl font-black text-white font-mono">{intentDist.tier_2_warm} Prospects</div>
            <p className="text-[11px] text-slate-400">Topic interest, API docs exploration, qualified for pain-point variant pitches.</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-700 space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400">Tier 3: Moderate Signal (&lt;80)</span>
            <div className="text-2xl font-black text-white font-mono">{intentDist.tier_3_mild} Prospects</div>
            <p className="text-[11px] text-slate-400">General ICP title match, targeted with educational and ROI benchmark hooks.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Analytics;
