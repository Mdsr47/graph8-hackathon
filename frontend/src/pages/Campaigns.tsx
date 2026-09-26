import React, { useState } from 'react';
import { Plus, Megaphone, Pause, Play, ArrowRight, Target, Sparkles, Send, Users, Clock } from 'lucide-react';
import { Campaign, ReferenceEmail } from '../types';

interface CampaignsProps {
  campaigns: Campaign[];
  referenceEmails: ReferenceEmail[];
  onSelectCampaign: (id: string) => void;
  onCreateCampaign: (name: string, icp: any, refIds: string[], dailyLimit: number, totalProspects: number) => Promise<void>;
  onToggleStatus: (id: string, currentStatus: string) => Promise<void>;
  onPushDailyBatch?: (id: string) => Promise<void>;
}

export const Campaigns: React.FC<CampaignsProps> = ({
  campaigns,
  referenceEmails,
  onSelectCampaign,
  onCreateCampaign,
  onToggleStatus,
  onPushDailyBatch,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('Fintech & Enterprise SaaS');
  const [titles, setTitles] = useState('VP Sales, Head of Sales, CRO, Founder');
  const [keywords, setKeywords] = useState('sales automation, deliverability, outbound intelligence');
  const [selectedRefIds, setSelectedRefIds] = useState<string[]>([]);
  const [totalProspects, setTotalProspects] = useState<number>(50);
  const [dailyLimit, setDailyLimit] = useState<number>(25);
  const [submitting, setSubmitting] = useState(false);
  const [pushingBatchId, setPushingBatchId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await onCreateCampaign(
        name,
        {
          industry,
          target_titles: titles.split(',').map((t) => t.trim()),
          keywords: keywords.split(',').map((k) => k.trim()),
        },
        selectedRefIds,
        dailyLimit,
        totalProspects
      );
      setIsModalOpen(false);
      setName('');
      setSelectedRefIds([]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerBatch = async (campId: string) => {
    if (!onPushDailyBatch) return;
    setPushingBatchId(campId);
    try {
      await onPushDailyBatch(campId);
    } finally {
      setPushingBatchId(null);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Campaigns</h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure ICP signals, total discovery cohort sizes, and automated daily sequence pacing.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition"
        >
          <Plus className="w-4 h-4" />
          <span>New Campaign</span>
        </button>
      </div>

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {campaigns.length === 0 ? (
          <div className="col-span-full p-12 text-center text-xs text-slate-500 rounded-2xl bg-slate-900 border border-slate-800">
            <Megaphone className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <p className="font-semibold text-slate-300">No campaigns created yet</p>
            <p className="mt-1 text-slate-500">Launch a campaign to discover prospects, formulate A/B variants, and start automated sequences.</p>
          </div>
        ) : (
          campaigns.map((c) => {
            const isPushing = pushingBatchId === c.id;
            return (
              <div
                key={c.id}
                className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-base font-bold text-white hover:text-indigo-400 transition cursor-pointer" onClick={() => onSelectCampaign(c.id)}>
                        {c.name}
                      </h3>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {c.icp_filters?.industry || 'B2B Software'}
                      </div>
                    </div>
                    <span
                      className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                        c.status === 'active'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : c.status === 'completed'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {c.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Cohort & Daily Pacing Pills */}
                  <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
                      <Users className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-500 uppercase font-semibold">Cohort Pool</div>
                        <div className="text-xs font-bold text-white font-mono">
                          {c.contacts_count || 0} / {c.target_contacts_limit || 50}
                        </div>
                      </div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-500 uppercase font-semibold">Daily Pacing</div>
                        <div className="text-xs font-bold text-cyan-300 font-mono">
                          {c.sent_today || 0} / {c.daily_limit || 25}/d
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Metrics Pills */}
                  <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800">
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                      <div className="text-xs font-bold text-white">{c.total_sends || 0}</div>
                      <div className="text-[10px] text-slate-500 uppercase">Sends</div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                      <div className="text-xs font-bold text-cyan-400">{c.total_replies || 0}</div>
                      <div className="text-[10px] text-slate-500 uppercase">Replies</div>
                    </div>
                    <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                      <div className="text-xs font-bold text-emerald-400">{c.total_positive || 0}</div>
                      <div className="text-[10px] text-slate-500 uppercase">Positive 🔥</div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-2 pt-4 mt-4 border-t border-slate-800">
                  {/* Push Daily Batch Button */}
                  {c.status === 'active' && onPushDailyBatch && (
                    <button
                      disabled={isPushing}
                      onClick={() => handleTriggerBatch(c.id)}
                      className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{isPushing ? 'Pushing Batch...' : 'Push Next Daily Batch Now'}</span>
                    </button>
                  )}

                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => onToggleStatus(c.id, c.status)}
                      className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
                    >
                      {c.status === 'active' ? (
                        <>
                          <Pause className="w-3.5 h-3.5 text-amber-400" />
                          <span>Pause</span>
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Resume</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => onSelectCampaign(c.id)}
                      className="flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
                    >
                      <span>Deep Dive</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Create Campaign Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 my-6">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Create New Outbound Campaign</h3>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Campaign Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Series B Fintech Expansion Outreach"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target ICP Industry</label>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Persona Job Titles (Comma-separated)</label>
                <input
                  type="text"
                  value={titles}
                  onChange={(e) => setTitles(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Intent Keywords to Monitor</label>
                <input
                  type="text"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* SEPARATE INPUT 1: Total Prospects To Fetch */}
              <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/30 space-y-1.5">
                <label className="block text-xs font-bold text-indigo-300">
                  Total Prospects to Fetch & Enrich (Stored in DB at once)
                </label>
                <input
                  type="number"
                  min={5}
                  max={500}
                  value={totalProspects}
                  onChange={(e) => setTotalProspects(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                />
                <span className="text-[11px] text-slate-400 block leading-tight">
                  All {totalProspects} intent-matched decision makers will be discovered and stored immediately in your Prospects tab.
                </span>
              </div>

              {/* SEPARATE INPUT 2: Daily Send Pacing Limit */}
              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/30 space-y-1.5">
                <label className="block text-xs font-bold text-cyan-300">
                  Daily Campaign Send Pacing Limit (Batch Size)
                </label>
                <input
                  type="number"
                  min={5}
                  max={200}
                  value={dailyLimit}
                  onChange={(e) => setDailyLimit(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[11px] text-slate-400 block leading-tight">
                  Autonomous scheduler pushes up to {dailyLimit} prospects into sequence per day until all {totalProspects} prospects are enrolled.
                </span>
              </div>

              {/* Reference Email Style Picker */}
              <div className="pt-2 border-t border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-white">
                    Style Reference Emails (Few-Shot Guides)
                  </label>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                    {selectedRefIds.length} Selected
                  </span>
                </div>
                <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                  {referenceEmails.length === 0 ? (
                    <div className="text-[11px] text-slate-500 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      No reference emails saved. Go to Reference Emails tab to add high-converting templates.
                    </div>
                  ) : (
                    referenceEmails.map((ref) => {
                      const isChecked = selectedRefIds.includes(ref.id);
                      return (
                        <label
                          key={ref.id}
                          className={`flex items-start gap-2.5 p-2 rounded-xl border text-xs cursor-pointer transition ${
                            isChecked
                              ? 'bg-indigo-950/40 border-indigo-500/50 text-white'
                              : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {
                              if (isChecked) {
                                setSelectedRefIds(selectedRefIds.filter((id) => id !== ref.id));
                              } else {
                                setSelectedRefIds([...selectedRefIds, ref.id]);
                              }
                            }}
                            className="mt-0.5 rounded text-indigo-600 focus:ring-0"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold truncate text-[11px] text-white">{ref.subject}</div>
                            <div className="text-[10px] text-slate-400 line-clamp-1">{ref.style_notes || ref.body}</div>
                          </div>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                <span>
                  Launching will discover and save all {totalProspects} prospects at once in your DB, then pause for your approval of the 2 A/B variants before starting the daily {dailyLimit}/day dispatch.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition"
                >
                  {submitting ? 'Launching...' : 'Launch & Auto-Enrich'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default Campaigns;
