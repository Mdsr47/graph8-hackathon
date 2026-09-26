import React, { useState, useMemo } from 'react';
import { Search, ExternalLink, Zap, ShieldCheck, CheckCircle2, ChevronRight, ChevronLeft, Filter, Tag, Building2, Briefcase } from 'lucide-react';
import { Contact } from '../types';

interface ProspectsProps {
  contacts: Contact[];
}

export const Prospects: React.FC<ProspectsProps> = ({ contacts }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  // Extract unique campaigns for filter dropdown
  const campaignOptions = useMemo(() => {
    const map = new Map<string, string>();
    contacts.forEach((c) => {
      if (c.campaign_id) {
        map.set(c.campaign_id, c.campaign_name || `Campaign ${c.campaign_id.slice(0, 8)}`);
      }
    });
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
  }, [contacts]);

  // Filtered contacts
  const filtered = useMemo(() => {
    return contacts.filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.company || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.email.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCampaign =
        selectedCampaignId === 'all' || c.campaign_id === selectedCampaignId;

      const matchesStatus =
        selectedStatus === 'all' || c.status === selectedStatus;

      return matchesSearch && matchesCampaign && matchesStatus;
    });
  }, [contacts, searchTerm, selectedCampaignId, selectedStatus]);

  // Pagination calculation
  const totalItems = filtered.length;
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const safeCurrentPage = Math.min(Math.max(currentPage, 1), totalPages);

  const paginatedContacts = useMemo(() => {
    const startIndex = (safeCurrentPage - 1) * pageSize;
    return filtered.slice(startIndex, startIndex + pageSize);
  }, [filtered, safeCurrentPage, pageSize]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
            Prospects & Intent Signals
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold border border-indigo-500/30">
              {totalItems} Discovered
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Intent-matched decision makers discovered from Graph8, linked by Campaign ID, and enriched with verified intelligence.
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Campaign Filter */}
          <div className="relative">
            <select
              value={selectedCampaignId}
              onChange={(e) => {
                setSelectedCampaignId(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="all">All Campaigns ({campaignOptions.length})</option>
              {campaignOptions.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="new">New (Pending Batch)</option>
            <option value="enrolled">Enrolled in Sequence</option>
            <option value="replied">Replied 🔥</option>
          </select>

          {/* Search Box */}
          <div className="relative w-full sm:w-56">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search name, company, role..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
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
                <th className="px-5 py-3.5">Campaign Name & ID</th>
                <th className="px-5 py-3.5">Intent Score</th>
                <th className="px-5 py-3.5">Outreach Status</th>
                <th className="px-5 py-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {paginatedContacts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    <p className="font-semibold text-slate-400">No matching prospects found</p>
                    <p className="text-[11px] text-slate-500 mt-1">
                      {contacts.length === 0
                        ? 'Launch a campaign to discover, verify, and store intent-matched decision makers here.'
                        : 'Try adjusting your search query or filters above.'}
                    </p>
                  </td>
                </tr>
              ) : (
                paginatedContacts.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => setSelectedContact(c)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    <td className="px-5 py-3.5 font-medium text-white">
                      <div className="font-semibold text-slate-100">{c.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{c.email}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="text-white font-medium flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.company || 'Enterprise Account'}</span>
                      </div>
                      <div className="text-slate-400 text-[11px]">{c.title || 'Executive'}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="text-indigo-300 font-medium text-xs truncate max-w-xs">
                        {c.campaign_name || 'Outbound Campaign'}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        ID: {c.campaign_id ? c.campaign_id.slice(0, 8) : 'N/A'}
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-14 h-2 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                            style={{ width: `${Math.min(c.intent_score, 100)}%` }}
                          />
                        </div>
                        <span className="font-bold text-indigo-400 font-mono text-xs">{c.intent_score}</span>
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
                        {c.status === 'new' ? 'PENDING BATCH' : c.status.toUpperCase()}
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

        {/* Pagination Bar */}
        {filtered.length > 0 && (
          <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span>Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none"
              >
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
              <span className="ml-2 font-mono text-slate-300">
                Showing {Math.min((safeCurrentPage - 1) * pageSize + 1, totalItems)} - {Math.min(safeCurrentPage * pageSize, totalItems)} of {totalItems}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                disabled={safeCurrentPage === 1}
                onClick={() => handlePageChange(safeCurrentPage - 1)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-300 transition"
                title="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              {/* Page numbers */}
              {Array.from({ length: Math.min(5, totalPages) }, (_, idx) => {
                let pageNum = idx + 1;
                if (totalPages > 5 && safeCurrentPage > 3) {
                  pageNum = safeCurrentPage - 2 + idx;
                  if (pageNum > totalPages) pageNum = totalPages - (4 - idx);
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`w-7 h-7 rounded-lg text-xs font-semibold font-mono transition ${
                      safeCurrentPage === pageNum
                        ? 'bg-indigo-600 text-white shadow'
                        : 'bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                disabled={safeCurrentPage === totalPages}
                onClick={() => handlePageChange(safeCurrentPage + 1)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-300 transition"
                title="Next Page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Enriched Intelligence Drawer Modal */}
      {selectedContact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-800/50">
              <div className="flex items-center gap-2.5">
                <Zap className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Graph8 Enriched Prospect</h3>
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

              {/* Campaign ID Relationship */}
              <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-1">
                <span className="text-[10px] text-indigo-300 uppercase font-bold block">Assigned Campaign</span>
                <div className="text-xs font-semibold text-white">{selectedContact.campaign_name || 'Outbound Campaign'}</div>
                <div className="text-[10px] text-slate-400 font-mono">Campaign ID: {selectedContact.campaign_id}</div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
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
export default Prospects;
