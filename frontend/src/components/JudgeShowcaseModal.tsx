import React, { useState } from 'react';
import {
  Trophy,
  X,
  Zap,
  ShieldCheck,
  BarChart3,
  Flame,
  Layers,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Sparkles,
  Mail,
  Cpu,
  RefreshCw,
  Target
} from 'lucide-react';

interface JudgeShowcaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (page: string) => void;
  onOpenSimulator: () => void;
}

export const JudgeShowcaseModal: React.FC<JudgeShowcaseModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onOpenSimulator,
}) => {
  const [activeTab, setActiveTab] = useState<'problem' | 'comparison' | 'superpowers' | 'architecture' | 'pitch'>('problem');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-5xl max-h-[92vh] flex flex-col bg-slate-900 border border-amber-500/40 rounded-2xl shadow-2xl overflow-hidden">
        {/* Top Gradient Ribbon */}
        <div className="h-2 bg-gradient-to-r from-amber-500 via-indigo-500 to-purple-500 shrink-0" />

        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/40">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/25 shrink-0">
              <Trophy className="w-6 h-6 text-slate-950 fill-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Hackathon Judge Showcase: Instantly & Apollo Competitor AI MVP
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Agentic RevOps Outbound
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                The world's first autonomous <strong className="text-slate-200">Self-Healing Outbound Agent</strong> powered by Graph8, LangGraph, and Groq LLM.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 gap-2 shrink-0 overflow-x-auto">
          {[
            { id: 'problem', label: '1. Problem Solved', icon: Target },
            { id: 'comparison', label: '2. Competitor Matrix', icon: Layers },
            { id: 'superpowers', label: '3. 5 Agentic Superpowers', icon: Zap },
            { id: 'architecture', label: '4. Live Architecture', icon: Cpu },
            { id: 'pitch', label: '5. 2-Min Judge Pitch', icon: Sparkles },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-3 px-4 border-b-2 text-sm font-semibold whitespace-nowrap transition ${
                  isActive
                    ? 'border-amber-400 text-amber-300 bg-amber-400/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: Problem Solved */}
          {activeTab === 'problem' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Traditional Outbound Failures */}
                <div className="p-5 rounded-xl bg-rose-950/20 border border-rose-500/30">
                  <div className="flex items-center gap-2 text-rose-400 font-semibold mb-3">
                    <XCircle className="w-5 h-5" />
                    <span>The Problem: Traditional Outbound (Instantly / Apollo)</span>
                  </div>
                  <ul className="text-sm text-slate-300 space-y-2.5">
                    <li className="flex items-start gap-2">
                      <span className="text-rose-400 font-bold">•</span>
                      <span><strong>Static Sequence Fatigue:</strong> Pre-scheduled 5-step email sequences blast prospects regardless of changing buyer intent.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-rose-400 font-bold">•</span>
                      <span><strong>Domain Deliverability Burn:</strong> When a variant copy is flagged as spam or receives negative replies, existing tools keep sending it until mailboxes are blacklisted.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-rose-400 font-bold">•</span>
                      <span><strong>Manual, Slow Iteration:</strong> RevOps leaders spend 10+ hours per week manually writing A/B variations and analyzing open rates without semantic insight.</span>
                    </li>
                  </ul>
                </div>

                {/* Graph8 Agent Breakthrough */}
                <div className="p-5 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-3">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>The Breakthrough: Graph8 Self-Healing Agent</span>
                  </div>
                  <ul className="text-sm text-slate-300 space-y-2.5">
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span><strong>Autonomous Reinforcement Loop:</strong> LangGraph agent evaluates live reply sentiments and dynamically kills underperforming variants.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span><strong>Evolutionary 15-Day Tournament:</strong> Continuously pitches Champion vs. Challenger copy, mutating winning angles into fresh variants.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span><strong>Human Clearance Governance:</strong> AI proposes copy mutations with transparent reasoning, awaiting human approval before firing.</span>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Core Value Proposition Card */}
              <div className="p-5 rounded-xl bg-slate-800/50 border border-slate-700">
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Why This Disrupts the \$12B Sales Engagement Market</span>
                </h4>
                <p className="text-sm text-slate-300 leading-relaxed">
                  While competitors treat cold email as a "dumb megaphone" with static templates and simple open-tracking pixels, the <strong className="text-white">Graph8 Self-Healing Outbound Agent</strong> treats cold outbound as an <strong className="text-indigo-400">adaptive cognitive feedback system</strong>. Every incoming reply, objection, or meeting booking feeds directly into our LLM decision engine to autonomously safeguard domain health, optimize pipeline conversion, and protect sender reputation.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: Competitor Matrix */}
          {activeTab === 'comparison' && (
            <div className="space-y-4">
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-300 uppercase tracking-wider border-b border-slate-800 font-semibold">
                    <tr>
                      <th className="py-3 px-4">Core Outbound Capability</th>
                      <th className="py-3 px-4 text-slate-400">Instantly.ai / Apollo.io</th>
                      <th className="py-3 px-4 text-amber-400 bg-amber-500/10 border-x border-amber-500/20">
                        Graph8 Self-Healing Agent
                      </th>
                      <th className="py-3 px-4">Agentic Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">Intent Discovery</td>
                      <td className="py-3 px-4 text-slate-400">Manual filter selection</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        Autonomous Graph8 API Topic & Keyword Telemetry
                      </td>
                      <td className="py-3 px-4 text-slate-300">Pulls live high-intent buyer signals without manual list uploads.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">Campaign Execution</td>
                      <td className="py-3 px-4 text-slate-400">Static scheduled sequences</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        Proportional Quota Daily Balancer (4/3 split)
                      </td>
                      <td className="py-3 px-4 text-slate-300">Prevents mailbox fatigue by pacing daily caps evenly across variants.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">A/B Testing Model</td>
                      <td className="py-3 px-4 text-slate-400">Manual 50/50 static split</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        15-Day Evolutionary Champion/Challenger Tournament
                      </td>
                      <td className="py-3 px-4 text-slate-300">Winner is promoted; loser is killed and replaced with mutated copy.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">Sentiment Telemetry</td>
                      <td className="py-3 px-4 text-slate-400">Opens & clicks only (vanity)</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        Groq LLM Semantic Sentiment & Objection Classification
                      </td>
                      <td className="py-3 px-4 text-slate-300">Detects positive, neutral, objections, and auto-drafts replies.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">Deliverability Protection</td>
                      <td className="py-3 px-4 text-slate-400">Warmup only; no copy auto-kill</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        Auto-Kill on Sentiment Dip + Variant C Generation
                      </td>
                      <td className="py-3 px-4 text-slate-300">Stops burning domains before spam filters catch on.</td>
                    </tr>
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">Safety & Oversight</td>
                      <td className="py-3 px-4 text-slate-400">Zero approval governance</td>
                      <td className="py-3 px-4 font-semibold text-emerald-400 bg-amber-500/5 border-x border-amber-500/20">
                        HITL Clearance Gate with Rejection Feedback Loop
                      </td>
                      <td className="py-3 px-4 text-slate-300">Users inspect copy, review reasoning, or reject with custom feedback.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: 5 Agentic Superpowers */}
          {activeTab === 'superpowers' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">1</div>
                  <h4 className="font-semibold text-white text-sm">Real-Time Intent Telemetry</h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Continuously pulls intent signals from Graph8 API (keywords, companies, topics). Automatically filters and enriches high-intent buyer contacts into local SQLite storage.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">2</div>
                  <h4 className="font-semibold text-white text-sm">Proportional Daily Quota Balancer</h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Enforces strict daily sending limits (e.g., 7 sends/day). Intelligently divides traffic (4 Variant A / 3 Variant B) and schedules subsequent batches automatically.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">3</div>
                  <h4 className="font-semibold text-white text-sm">15-Day Evolutionary Tournament</h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Tracks Champion vs Challenger performance across an automated 15-day cycle. Calculates dynamic conversion scores and generates detailed daily progress updates.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold">4</div>
                  <h4 className="font-semibold text-white text-sm">Self-Healing Variant C Mutation</h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  When a variant copy receives negative replies or zero engagement, the LangGraph agent kills it, analyzes the objections, and mutates an evolved Variant C for clearance.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700 md:col-span-2">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold">5</div>
                  <h4 className="font-semibold text-white text-sm">Dual Mailbox Architecture & Human Clearance</h4>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Empowers users with direct SMTP/IMAP custom configuration for independent send/receive capabilities while simultaneously orchestrating Graph8 programmatic campaigns, fully protected by a Human-in-the-Loop approval gate with iterative feedback rejection loops.
                </p>
              </div>
            </div>
          )}

          {/* TAB 4: Architecture */}
          {activeTab === 'architecture' && (
            <div className="space-y-4">
              <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
                <div className="text-amber-400 font-bold mb-3 flex items-center gap-2">
                  <Cpu className="w-4 h-4" />
                  <span>CLOSED-LOOP REINFORCEMENT ARCHITECTURE</span>
                </div>
                <div className="space-y-2 text-slate-300">
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-indigo-400 font-semibold">[1. INGESTION]</span> Graph8 Intent Telemetry &rarr; Prospect Contacts &amp; Keywords Enriched in SQLite
                  </div>
                  <div className="text-center text-slate-500">&darr;</div>
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-emerald-400 font-semibold">[2. GENERATION]</span> Groq LLM creates 2 contrasting angles (Variant A &amp; B) based on reference winners
                  </div>
                  <div className="text-center text-slate-500">&darr;</div>
                  <div className="p-2.5 rounded bg-slate-900 border border-amber-500/40">
                    <span className="text-amber-400 font-semibold">[3. HUMAN GATE]</span> HITL Clearance Gate: Approve &rarr; Launch or Reject &rarr; Instant Feedback Regeneration Loop
                  </div>
                  <div className="text-center text-slate-500">&darr;</div>
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-purple-400 font-semibold">[4. DISPATCH]</span> Daily Quota Balancer dispatches proportional batches (4/3) via Graph8 API &amp; SMTP
                  </div>
                  <div className="text-center text-slate-500">&darr;</div>
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                    <span className="text-rose-400 font-semibold">[5. TELEMETRY]</span> Inbound Webhook / IMAP Sync &rarr; Semantic LLM Sentiment &amp; Objection Classification
                  </div>
                  <div className="text-center text-slate-500">&darr;</div>
                  <div className="p-2.5 rounded bg-slate-900 border border-emerald-500/40">
                    <span className="text-emerald-400 font-semibold">[6. SELF-HEALING]</span> LangGraph Reinforcement Cycle: Kill underperforming copy &rarr; Mutate Variant C &rarr; Rebalance
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: 2-Minute Pitch */}
          {activeTab === 'pitch' && (
            <div className="space-y-4">
              <div className="p-5 rounded-xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/30">
                <h4 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  <span>The 2-Minute Executive Pitch for Hackathon Judges</span>
                </h4>
                <div className="space-y-3 text-sm text-slate-300 leading-relaxed">
                  <p>
                    <strong className="text-amber-300">1. Hook:</strong> "Every B2B company using Instantly or Apollo faces the same nightmare: static campaigns blast prospects with outdated copy, ruin domain reputation, and burn through TAM."
                  </p>
                  <p>
                    <strong className="text-emerald-300">2. Solution:</strong> "We built the Graph8 Self-Healing Outbound Agent. It operates like an autonomous RevOps engineer in a box. It pulls real-time buyer intent signals, generates high-converting contrasting variants, and submits them to an approval gate."
                  </p>
                  <p>
                    <strong className="text-purple-300">3. The Agentic Magic:</strong> "Once launched, our LangGraph reinforcement loop monitors replies in real time. If sentiment drops or objections arise, the agent automatically kills the failing variant, mutates copy into an evolved Variant C, and rebalances sending quotas."
                  </p>
                  <p>
                    <strong className="text-sky-300">4. Live Impact:</strong> "Zero burned domains. Zero manual A/B split guessing. 100% autonomous outbound optimization backed by human clearance."
                  </p>
                </div>
              </div>

              {/* Quick Interactive Actions */}
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700">
                <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Test Live Capabilities Right Now:
                </h5>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    onClick={() => { onClose(); onNavigate('analytics'); }}
                    className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 text-center transition flex flex-col items-center gap-1.5"
                  >
                    <BarChart3 className="w-4 h-4 text-indigo-400" />
                    <span>Variant Analytics</span>
                  </button>
                  <button
                    onClick={() => { onClose(); onNavigate('approvals'); }}
                    className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 text-center transition flex flex-col items-center gap-1.5"
                  >
                    <ShieldCheck className="w-4 h-4 text-amber-400" />
                    <span>HITL Approvals</span>
                  </button>
                  <button
                    onClick={() => { onClose(); onOpenSimulator(); }}
                    className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 text-center transition flex flex-col items-center gap-1.5"
                  >
                    <Zap className="w-4 h-4 text-emerald-400" />
                    <span>Webhook Simulator</span>
                  </button>
                  <button
                    onClick={() => { onClose(); onNavigate('inbox'); }}
                    className="p-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 text-center transition flex flex-col items-center gap-1.5"
                  >
                    <Mail className="w-4 h-4 text-purple-400" />
                    <span>Inbox &amp; Replies</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between shrink-0">
          <div className="text-xs text-slate-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live SQLite Database &bull; Groq LLM &bull; Graph8 API Active</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition"
          >
            Explore Dashboard &rarr;
          </button>
        </div>
      </div>
    </div>
  );
};
