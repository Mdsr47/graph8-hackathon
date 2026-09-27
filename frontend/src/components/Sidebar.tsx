import React from 'react';
import {
  LayoutDashboard,
  Megaphone,
  BarChart3,
  Users,
  Inbox,
  BrainCircuit,
  ShieldCheck,
  MailCheck,
  Settings,
  Sparkles,
  Zap,
  Trophy,
  LogOut,
  User as UserIcon
} from 'lucide-react';
import { User } from '../types';

interface SidebarProps {
  activePage: string;
  setActivePage: (page: string) => void;
  pendingApprovalsCount: number;
  inboxCount: number;
  currentUser?: User | null;
  onLogout?: () => void;
  onOpenJudgeShowcase?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  setActivePage,
  pendingApprovalsCount,
  inboxCount,
  currentUser,
  onLogout,
  onOpenJudgeShowcase,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'campaigns', label: 'Campaigns', icon: Megaphone },
    { id: 'analytics', label: 'Variant Analytics', icon: BarChart3 },
    { id: 'prospects', label: 'Prospects & Signals', icon: Users },
    { id: 'inbox', label: 'Inbox & Replies', icon: Inbox, badge: inboxCount > 0 ? inboxCount : null, badgeColor: 'bg-emerald-500' },
    { id: 'decisions', label: 'Agent Decisions', icon: BrainCircuit },
    { id: 'approvals', label: 'HITL Approvals', icon: ShieldCheck, badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : null, badgeColor: 'bg-amber-500 animate-pulse' },
    { id: 'reference-emails', label: 'Reference Emails', icon: MailCheck },
    { id: 'settings', label: 'Settings & Mailbox', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col shrink-0 h-screen select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              graph8 <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-semibold border border-indigo-500/30">AGENT</span>
            </div>
            <div className="text-[11px] text-slate-400 font-medium">Self-Healing Outbound</div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full text-white ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Judge Showcase Quick Nav Item */}
        {onOpenJudgeShowcase && (
          <div className="pt-2">
            <button
              onClick={onOpenJudgeShowcase}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-bold text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 transition shadow-sm"
            >
              <div className="flex items-center gap-2">
                <Trophy className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                <span>🏆 Judge Showcase</span>
              </div>
              <span className="text-[10px] uppercase tracking-wider text-amber-400 font-extrabold">MVP</span>
            </button>
          </div>
        )}
      </nav>

      {/* User Profile Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60 space-y-2">
        {currentUser && (
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 border border-slate-700/60">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-amber-500 flex items-center justify-center font-bold text-xs text-white shrink-0 shadow-sm">
                {currentUser.name ? currentUser.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'AV'}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-100 truncate">{currentUser.name || 'Alex Vance'}</div>
                <div className="text-[10px] text-slate-400 truncate">{currentUser.role || 'Lead RevOps'}</div>
              </div>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="p-1.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-700/60 transition shrink-0"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {/* Autonomous Status Micro-Card */}
        <div className="p-2.5 rounded-lg bg-slate-800/30 border border-slate-800 flex items-center gap-2 text-[11px] text-slate-400">
          <Sparkles className="w-3 h-3 text-indigo-400 shrink-0" />
          <span className="truncate">LangGraph Reinforcement Loop Active</span>
        </div>
      </div>
    </aside>
  );
};
