import React from 'react';
import { Radio, Play, PlusCircle, Activity } from 'lucide-react';

interface HeaderProps {
  isConnected: boolean;
  onOpenSimulator: () => void;
  onNewCampaign: () => void;
  activeCampaignsCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  onOpenSimulator,
  onNewCampaign,
  activeCampaignsCount,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
      {/* Left: Status Badges */}
      <div className="flex items-center gap-4">
        {/* SSE Live Pulse */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
          <span className="relative flex h-2 w-2">
            {isConnected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </span>
          <span className="font-medium text-slate-300">
            {isConnected ? 'Real-Time SSE Stream Active' : 'Connecting to Stream...'}
          </span>
        </div>

        {/* Active Campaigns Counter */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          <span>Active Campaigns: <strong className="text-white font-semibold">{activeCampaignsCount}</strong></span>
        </div>
      </div>

      {/* Right: Quick Actions */}
      <div className="flex items-center gap-3">
        {/* Interactive Webhook Simulator Button */}
        <button
          onClick={onOpenSimulator}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold transition"
          title="Simulate inbound webhook telemetry for demo"
        >
          <Play className="w-3.5 h-3.5 fill-amber-300" />
          <span>Demo Webhook Simulator</span>
        </button>

        {/* New Campaign Button */}
        <button
          onClick={onNewCampaign}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/25 transition"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Launch Campaign</span>
        </button>
      </div>
    </header>
  );
};
