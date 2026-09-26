import React, { useState } from 'react';
import { Search, ExternalLink, Zap, ShieldCheck, CheckCircle2, ChevronRight, X } from 'lucide-react';
import { Contact } from '../types';

interface ProspectsProps {
  contacts: Contact[];
}

export const Prospects: React.FC<ProspectsProps> = ({ contacts }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  const filtered = contacts.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.title || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Prospects & Intent Signals</h1>
          <p className="text-xs text-slate-400 mt-1">
            Decision makers discovered via graph8 intent keywords and enriched with verified intelligence.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search prospect or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Prospects Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
              <tr>
                <th className="px-5 py-3.5">Prospect</th>
                <th className="px-5 py-3.5">Company & Role</th>
                <th className="px-5 py-3.5">Intent Score</th>
                <th className="px-5 py-3.5">Outbound Status</th>
                <th className="px-5 py-3.5 text-right">Enrichment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center text-slate-500">
                    <p className="font-semibold text-slate-400">No prospects in database yet</p>
                    <p className="text-[11px] text-slate-500 mt-1">Launch a campaign to discover, verify, and store intent-matched decision makers here.</p>
                  </td>
                </tr>
              ) : (
                filtered.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => setSelectedContact(c)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    <td className="px-5 py-3.5 font-medium text-white">
                      <div>{c.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{c.email}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="text-white font-medium">{c.company || 'Enterprise Account'}</div>
                      <div className="text-slate-400 text-[11px]">{c.title || 'Executive'}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                            style={{ width: `${Math.min(c.intent_score, 100)}%` }}
                          />
                        </div>
                        <span className="font-bold text-indigo-400 font-mono">{c.intent_score}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                          c.status === 'replied'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : c.status === 'enrolled'
                            ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button className="text-slate-400 hover:text-white transition">
                        <ChevronRight className="w-4 h-4 ml-auto" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enriched Intelligence Drawer Modal */}
      {selectedContact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
              <div className="flex items-center gap-2.5">
                <Zap className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">graph8 Enriched Intelligence</h3>
              </div>
              <button onClick={() => setSelectedContact(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div>
                <h4 className="text-sm font-bold text-white">{selectedContact.name}</h4>
                <p className="text-slate-400">{selectedContact.title} at {selectedContact.company}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-indigo-400 font-mono">{selectedContact.email}</span>
                  {selectedContact.enriched_data?.linkedin_url && (
                    <a
                      href={selectedContact.enriched_data.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] text-blue-400 hover:underline flex items-center gap-0.5"
                    >
                      <span>LinkedIn Profile</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800">
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Intent Score</span>
                  <div className="text-base font-bold text-emerald-400">{selectedContact.intent_score} / 100</div>
                  <span className="text-[10px] text-slate-400">High buying velocity</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block mb-1">Funding & Stage</span>
                  <div className="text-base font-bold text-white">
                    {selectedContact.enriched_data?.recent_funding || 'Series B ($28M)'}
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {selectedContact.enriched_data?.company_size || 'Revenue expansion'}
                  </span>
                </div>
              </div>

              {selectedContact.enriched_data?.tech_stack && (
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Detected Tech Stack:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedContact.enriched_data.tech_stack.map((t, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedContact.enriched_data?.key_priorities && (
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 space-y-1">
                  <span className="font-semibold block mb-1">Identified Key Priorities:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px] text-indigo-200">
                    {selectedContact.enriched_data.key_priorities.map((p, idx) => (
                      <li key={idx}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-800/30 flex justify-end">
              <button
                onClick={() => setSelectedContact(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
