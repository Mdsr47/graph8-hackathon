import React from 'react';
import { BrainCircuit, ShieldAlert, CheckCircle2, ChevronDown, ArrowRight } from 'lucide-react';
import { AgentDecision } from '../types';

interface DecisionsProps {
  decisions: AgentDecision[];
}

export const Decisions: React.FC<DecisionsProps> = ({ decisions }) => {
  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
          Agent Decisions & Explainability Log
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
            Audit Trail
          </span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Every autonomous and reinforced decision executed by the LangGraph agent is immutably logged with reasoning and state diffs.
        </p>
      </div>

      {/* Decisions Timeline */}
      <div className="space-y-4">
        {decisions.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 rounded-2xl bg-slate-900 border border-slate-800">
            No decisions logged yet. Decisions will appear as the agent discovers accounts and triggers reinforcement cycles.
          </div>
        ) : (
          decisions.map((d) => {
            const isKill = d.decision_type.includes('kill');
            const isGenerate = d.decision_type.includes('generate');
            const isApproved = d.decision_type.includes('hitl');

            return (
              <div
                key={d.id}
                className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                        isKill
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : isApproved
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      }`}
                    >
                      <BrainCircuit className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                        {d.decision_type.replace('_', ' ')}
                      </h3>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(d.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {d.requires_approval ? (
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" /> HITL GATE ENFORCED
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                        AUTONOMOUS
                      </span>
                    )}
                  </div>
                </div>

                {/* Reasoning Quote */}
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    AI Decision Rationale:
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {d.reasoning}
                  </p>
                </div>

                {/* State Diff / Payload */}
                {(d.before_state || d.after_state) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] pt-1">
                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                      <span className="text-[10px] font-mono text-slate-500 block mb-1">Before State:</span>
                      <pre className="text-slate-400 font-mono overflow-x-auto text-[10px]">
                        {JSON.stringify(d.before_state, null, 2)}
                      </pre>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800">
                      <span className="text-[10px] font-mono text-emerald-400 block mb-1">After State:</span>
                      <pre className="text-emerald-300 font-mono overflow-x-auto text-[10px]">
                        {JSON.stringify(d.after_state, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
