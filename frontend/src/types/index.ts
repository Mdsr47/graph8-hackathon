export interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  icp_filters: {
    industry?: string;
    target_titles?: string[];
    company_size?: string;
    keywords?: string[];
  };
  reference_email_ids?: string[];
  daily_limit?: number;
  target_contacts_limit?: number;
  sent_today?: number;
  last_batch_run_at?: string;
  created_at: string;
  contacts_count?: number;
  variants_count?: number;
  total_sends?: number;
  total_replies?: number;
  total_positive?: number;
  total_meetings?: number;
  reply_rate?: number;
}

export interface Contact {
  id: string;
  campaign_id: string;
  campaign_name?: string;
  graph8_contact_id?: string;
  name: string;
  email: string;
  title?: string;
  company?: string;
  intent_score: number;
  current_step: number;
  status: 'new' | 'enrolled' | 'replied' | 'bounced' | 'meeting_booked';
  enriched_data?: {
    verified?: boolean;
    linkedin_url?: string;
    tech_stack?: string[];
    recent_funding?: string;
    key_priorities?: string[];
    company_size?: string;
    annual_revenue?: string;
  };
  created_at: string;
}

export interface Variant {
  id: string;
  campaign_id: string;
  channel: string;
  subject: string;
  body_template: string;
  status: 'active' | 'killed' | 'draft';
  sends_count: number;
  opens_count: number;
  replies_count: number;
  positive_replies_count: number;
  meetings_count: number;
  score?: number;
  allocation_percentage?: number;
  created_at: string;
  killed_at?: string;
  open_rate?: number;
  reply_rate?: number;
  positive_reply_rate?: number;
}

export interface EventItem {
  id: string;
  contact_id?: string;
  variant_id?: string;
  event_type: 'sent' | 'opened' | 'replied' | 'bounced' | 'meeting_booked';
  raw_payload?: any;
  sentiment?: 'positive' | 'neutral' | 'negative';
  created_at: string;
}

export interface AgentDecision {
  id: string;
  campaign_id: string;
  decision_type: string;
  reasoning: string;
  before_state: any;
  after_state: any;
  requires_approval: boolean;
  created_at: string;
}

export interface Approval {
  id: string;
  decision_id?: string;
  type: 'send_new_variant' | 'kill_variant' | 'send_replacement_variant' | 'voice_escalation' | 'reply_draft';
  payload: any;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  resolved_at?: string;
}

export interface ReferenceEmail {
  id: string;
  subject: string;
  body: string;
  style_notes?: string;
  created_at: string;
}

export interface InboxItem {
  id: string;
  contact_id?: string;
  contact_name: string;
  contact_email: string;
  company: string;
  subject: string;
  body: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  status: string;
  received_at: string;
  ai_draft_reply?: string;
}

export interface SettingsData {
  graph8_api_key_status: string;
  graph8_base_url: string;
  llm_provider: string;
  llm_model: string;
  llm_base_url: string;
  llm_api_key_status: string;
  supabase_configured: boolean;
  webhook_url: string;
  simulation_mode: boolean;
  voice_escalation: {
    enabled: boolean;
    badge: string;
    threshold: number;
  };
  mailbox: {
    id?: string;
    provider: string;
    email: string;
    status: string;
    warmup_enabled?: boolean;
    daily_limit?: number;
    sent_today?: number;
  };
  graph8_mailbox_settings_url: string;
}

export interface MailboxConfig {
  configured?: boolean;
  provider: 'gmail' | 'outlook' | 'custom';
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password?: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  imap_password?: string;
  imap_use_ssl: boolean;
  from_name: string;
  from_email: string;
  status: 'connected' | 'disconnected' | 'error';
  last_synced_at?: string;
}

export interface OverviewStats {
  prospects_enriched: number;
  outbound_sends: number;
  total_inbound_replies: number;
  positive_sentiment: number;
  meetings_booked: number;
  pending_approvals: number;
}

export interface VariantMetrics {
  sent: number;
  delivered: number;
  deliveryRate: number;
  opens: number;
  openRate: number;
  clicks: number;
  clickRate: number;
  replies: number;
  replyRate: number;
  positiveReplies: number;
  positiveReplyRate: number;
  bounces: number;
  bounceRate: number;
  meetings: number;
}

export interface VariantAnalyticsItem {
  variant_id: string;
  campaign_id: string;
  campaign_name: string;
  channel: string;
  subject: string;
  body_template: string;
  status: 'active' | 'killed' | 'draft';
  score: number;
  allocation_percentage: number;
  metrics: VariantMetrics;
}

export interface AnalyticsSummary {
  total_sends: number;
  total_delivered: number;
  delivery_rate: number;
  total_opens: number;
  open_rate: number;
  total_clicks: number;
  click_rate: number;
  total_replies: number;
  reply_rate: number;
  total_positive: number;
  positive_reply_rate: number;
  total_bounces: number;
  bounce_rate: number;
  total_meetings: number;
  total_prospects: number;
  total_variants: number;
}

export interface AnalyticsData {
  summary: AnalyticsSummary;
  variants: VariantAnalyticsItem[];
  intent_distribution: {
    tier_1_hot: number;
    tier_2_warm: number;
    tier_3_mild: number;
  };
  campaigns: Array<{
    id: string;
    name: string;
    status: string;
    daily_limit: number;
    target_contacts_limit: number;
    sent_today: number;
    last_batch_run_at?: string;
  }>;
}
