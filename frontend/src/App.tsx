import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { SimulatorModal } from './components/SimulatorModal';
import { ApprovalModal } from './components/ApprovalModal';

// Pages
import { Overview } from './pages/Overview';
import { Campaigns } from './pages/Campaigns';
import { CampaignDetail } from './pages/CampaignDetail';
import { Analytics } from './pages/Analytics';
import { Prospects } from './pages/Prospects';
import { Inbox } from './pages/Inbox';
import { Decisions } from './pages/Decisions';
import { Approvals } from './pages/Approvals';
import { ReferenceEmails } from './pages/ReferenceEmails';
import { Settings } from './pages/Settings';

import { useLiveFeed } from './hooks/useLiveFeed';
import {
  Campaign,
  Contact,
  AgentDecision,
  Approval,
  InboxItem,
  ReferenceEmail,
  SettingsData,
  OverviewStats
} from './types';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('overview');
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);

  // Data states
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [decisions, setDecisions] = useState<AgentDecision[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [inboxItems, setInboxItems] = useState<InboxItem[]>([]);
  const [referenceEmails, setReferenceEmails] = useState<ReferenceEmail[]>([]);
  const [settingsData, setSettingsData] = useState<SettingsData | null>(null);
  const [overviewStats, setOverviewStats] = useState<OverviewStats | null>(null);

  // Modals
  const [isSimulatorOpen, setIsSimulatorOpen] = useState(false);
  const [activeApprovalModal, setActiveApprovalModal] = useState<Approval | null>(null);

  // Fetch all core data
  const fetchAllData = async () => {
    try {
      const [cRes, pRes, dRes, aRes, iRes, rRes, sRes, stRes] = await Promise.all([
        fetch('/api/campaigns'),
        fetch('/api/prospects'),
        fetch('/api/decisions?limit=50'),
        fetch('/api/approvals'),
        fetch('/api/inbox'),
        fetch('/api/reference-emails'),
        fetch('/api/settings'),
        fetch('/api/stats'),
      ]);

      if (cRes.ok) setCampaigns(await cRes.json());
      if (pRes.ok) setContacts(await pRes.json());
      if (dRes.ok) setDecisions(await dRes.json());
      if (aRes.ok) setApprovals(await aRes.json());
      if (iRes.ok) setInboxItems(await iRes.json());
      if (rRes.ok) setReferenceEmails(await rRes.json());
      if (sRes.ok) setSettingsData(await sRes.json());
      if (stRes.ok) setOverviewStats(await stRes.json());
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000); // Polling backup
    return () => clearInterval(interval);
  }, []);

  // SSE Live Feed Hook
  const { isConnected, activities } = useLiveFeed((eventType, data) => {
    // Dynamically update states on real-time SSE arrival
    if (eventType === 'agent_decision') {
      setDecisions(prev => [data, ...prev]);
    } else if (eventType === 'approval_created') {
      setApprovals(prev => [data, ...prev]);
    } else if (eventType === 'approval_resolved') {
      setApprovals(prev => prev.map(a => a.id === data.id ? { ...a, status: data.status } : a));
    } else if (eventType === 'webhook_event' || eventType === 'database_reset') {
      fetchAllData();
    }
  });

  const handleResetDatabase = async () => {
    try {
      const res = await fetch('/api/settings/reset-database', { method: 'POST' });
      if (res.ok) {
        await fetchAllData();
      }
    } catch (err) {
      console.error('Failed to reset database:', err);
    }
  };

  // Actions
  const handleSelectCampaign = (id: string) => {
    setSelectedCampaignId(id);
    setActivePage('campaign-detail');
  };

  const handleCreateCampaign = async (name: string, icp: any, refIds: string[] = [], dailyLimit: number = 25, totalProspects: number = 50) => {
    const res = await fetch('/api/campaigns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        icp_filters: icp,
        reference_email_ids: refIds,
        daily_limit: dailyLimit,
        target_contacts_limit: totalProspects,
      }),
    });
    if (res.ok) {
      await fetchAllData();
      setActivePage('campaigns');
    }
  };

  const handlePushDailyBatch = async (campaignId: string) => {
    const res = await fetch(`/api/campaigns/${campaignId}/run-daily-batch`, { method: 'POST' });
    if (res.ok) {
      await fetchAllData();
    }
  };

  const handleToggleStatus = async (id: string, currentStatus: string) => {
    const endpoint = currentStatus === 'active' ? `/api/campaigns/${id}/pause` : `/api/campaigns/${id}/resume`;
    await fetch(endpoint, { method: 'POST' });
    await fetchAllData();
  };

  const handleSimulateTelemetry = async (eventType: string, sentiment?: string, replyText?: string) => {
    await fetch('/api/webhooks/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_id: selectedCampaignId || campaigns[0]?.id,
        event_type: eventType,
        sentiment: sentiment,
        reply_text: replyText,
      }),
    });
    await fetchAllData();
  };

  const handleResolveApproval = async (id: string, status: 'approved' | 'rejected', notes?: string, editedPayload?: any) => {
    await fetch(`/api/approvals/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, notes, edited_payload: editedPayload }),
    });
    await fetchAllData();
  };

  const handleGenerateDraft = async (id: string) => {
    const res = await fetch(`/api/inbox/${id}/draft`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      await fetchAllData();
      return data.ai_draft_reply || '';
    }
    return '';
  };

  const handleSendReply = async (id: string, text: string) => {
    await fetch(`/api/inbox/${id}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reply_id: id, text }),
    });
    await fetchAllData();
  };

  const handleSyncInbox = async () => {
    const res = await fetch('/api/mailboxes/sync', { method: 'POST' });
    if (res.ok) {
      await fetchAllData();
    } else {
      const err = await res.json();
      throw new Error(err.detail || 'IMAP sync failed');
    }
  };

  const handleComposeEmail = async (to: string, subject: string, body: string) => {
    const res = await fetch('/api/inbox/compose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to_email: to, subject, body }),
    });
    if (res.ok) {
      await fetchAllData();
    } else {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to send outbound email via SMTP');
    }
  };

  const handleAddRefEmail = async (subject: string, body: string, notes?: string) => {
    await fetch('/api/reference-emails', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body, style_notes: notes }),
    });
    await fetchAllData();
  };

  const handleDeleteRefEmail = async (id: string) => {
    await fetch(`/api/reference-emails/${id}`, { method: 'DELETE' });
    await fetchAllData();
  };

  const pendingApprovalsCount = approvals.filter(a => a.status === 'pending').length;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage === 'campaign-detail' ? 'campaigns' : activePage}
        setActivePage={(page) => {
          setSelectedCampaignId(null);
          setActivePage(page);
        }}
        pendingApprovalsCount={pendingApprovalsCount}
        inboxCount={inboxItems.length}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          isConnected={isConnected}
          onOpenSimulator={() => setIsSimulatorOpen(true)}
          onNewCampaign={() => setActivePage('campaigns')}
          activeCampaignsCount={campaigns.filter(c => c.status === 'active').length}
        />

        {/* Dynamic Page Router */}
        <main className="flex-1 overflow-y-auto">
          {activePage === 'overview' && (
            <Overview
              campaigns={campaigns}
              contacts={contacts}
              stats={overviewStats}
              decisions={decisions}
              approvals={approvals}
              liveActivities={activities}
              onSelectCampaign={handleSelectCampaign}
              onNavigatePage={setActivePage}
            />
          )}

          {activePage === 'campaigns' && (
            <Campaigns
              campaigns={campaigns}
              referenceEmails={referenceEmails}
              onSelectCampaign={handleSelectCampaign}
              onCreateCampaign={handleCreateCampaign}
              onToggleStatus={handleToggleStatus}
              onPushDailyBatch={handlePushDailyBatch}
            />
          )}

          {activePage === 'campaign-detail' && selectedCampaignId && (
            <CampaignDetail
              campaignId={selectedCampaignId}
              onBack={() => setActivePage('campaigns')}
            />
          )}

          {activePage === 'analytics' && (
            <Analytics />
          )}

          {activePage === 'prospects' && (
            <Prospects contacts={contacts} />
          )}

          {activePage === 'inbox' && (
            <Inbox
              inboxItems={inboxItems}
              onGenerateDraft={handleGenerateDraft}
              onSendReply={handleSendReply}
              onNavigateApprovals={() => setActivePage('approvals')}
              onSyncInbox={handleSyncInbox}
              onComposeEmail={handleComposeEmail}
            />
          )}

          {activePage === 'decisions' && (
            <Decisions decisions={decisions} />
          )}

          {activePage === 'approvals' && (
            <Approvals
              approvals={approvals}
              onOpenApprovalModal={(appr) => setActiveApprovalModal(appr)}
              onQuickResolve={(id, status) => handleResolveApproval(id, status)}
            />
          )}

          {activePage === 'reference-emails' && (
            <ReferenceEmails
              referenceEmails={referenceEmails}
              onAddEmail={handleAddRefEmail}
              onDeleteEmail={handleDeleteRefEmail}
            />
          )}

          {activePage === 'settings' && settingsData && (
            <Settings
              settings={settingsData}
              onRefreshMailbox={fetchAllData}
              onResetDatabase={handleResetDatabase}
            />
          )}
        </main>
      </div>

      {/* Simulator Modal */}
      <SimulatorModal
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
        campaigns={campaigns}
        onTriggerSimulate={handleSimulateTelemetry}
      />

      {/* Approval Modal */}
      <ApprovalModal
        approval={activeApprovalModal}
        onClose={() => setActiveApprovalModal(null)}
        onResolve={handleResolveApproval}
      />
    </div>
  );
};
export default App;
