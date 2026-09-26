# n8n Automation Layer — graph8 Self-Healing Outbound Relay

> **Scope Note:** The core self-healing outbound agent, LangGraph cyclical loop, and live dashboard are completely self-sufficient and do **NOT** require n8n to function.
> This optional n8n workflow is designed as an external **visual automation and notification relay** layer that adds flair for hackathon judges by sending rich Slack/Discord alerts and pulling account intelligence via graph8's MCP endpoint.

---

## Architecture Diagram

```
graph8 Webhook Receiver (or Backend Relay)
           │
           ▼
┌───────────────────────────┐
│ 1. Webhook Trigger Node   │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 2. IF / Switch Node       │ ──[Not Positive Reply]──> End / Log
└─────────────┬─────────────┘
              │ [event_type == 'replied' && sentiment == 'positive']
              ▼
┌───────────────────────────┐
│ 3. HTTP Request (MCP)     │ --> Hits graph8 MCP endpoint: POST /api/v1/mcp
│    Tool: get_account      │     Pulls annual revenue, funding, employee count
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 4. Slack / Discord Node   │ --> Posts "🔥 Positive reply from Sarah Jenkins (VP Sales)
│    Channel: #revops-alerts│     at FintechFlow ($28M Series B) — Demo Requested!"
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 5. HTTP Request (Backend) │ --> Calls backend /api/campaigns/{id}/reallocate
│    Party Trick Trigger    │     Triggers instant reinforcement optimization
└───────────────────────────┘
```

---

## Node-by-Node Setup Guide

### Node 1: Webhook Trigger
- **Type**: `n8n-nodes-base.webhook`
- **Method**: `POST`
- **Path**: `graph8-relay`
- **Response Code**: `200`
- **Response Body**: `{"status": "received"}`
- **Example Input Payload**:
```json
{
  "event_type": "replied",
  "contact_id": "cnt_g8_01",
  "campaign_id": "camp_demo_01",
  "from_name": "Sarah Jenkins",
  "from_email": "sarah.jenkins@fintechflow.io",
  "company": "FintechFlow Inc",
  "subject": "Re: Quick question regarding outbound pipeline",
  "text": "Hi Alex, we would love to see a demo Thursday 2pm EST!",
  "sentiment": "positive"
}
```

### Node 2: IF / Switch Condition
- **Type**: `n8n-nodes-base.if`
- **Condition 1**: `{{ $json.event_type }}` equals `replied`
- **Condition 2**: `{{ $json.sentiment }}` equals `positive`
- **Combine Mode**: `AND`

### Node 3: graph8 MCP Account Intelligence
- **Type**: `n8n-nodes-base.httpRequest`
- **Method**: `POST`
- **URL**: `https://be.graph8.com/api/v1/mcp`
- **Authentication**: Header Auth (`Authorization: Bearer {{ $credentials.graph8ApiKey }}`)
- **Body Parameters**:
```json
{
  "tool": "get_account",
  "arguments": {
    "domain": "{{ $json.from_email.split('@')[1] }}",
    "company_name": "{{ $json.company }}"
  }
}
```
- **Example Output**:
```json
{
  "company": "FintechFlow Inc",
  "funding": "Series B ($28M)",
  "headcount": 240,
  "industry": "Financial Technology",
  "decision_maker": "Sarah Jenkins (VP Revenue Operations)"
}
```

### Node 4: Slack / Discord Team Alert
- **Type**: `n8n-nodes-base.slack` (or Discord Webhook)
- **Channel**: `#revops-hot-leads`
- **Message Text**:
```
🔥 *Hot Lead Inbound Alert — graph8 Self-Healing Outbound*
*Prospect:* {{ $('Webhook Trigger').item.json.from_name }} ({{ $('Webhook Trigger').item.json.company }})
*Email:* `{{ $('Webhook Trigger').item.json.from_email }}`
*Sentiment:* Positive 🔥
*Reply:* "{{ $('Webhook Trigger').item.json.text }}"
*Account Intelligence:* {{ $json.funding }} • {{ $json.headcount }} employees • {{ $json.industry }}
👉 *Action:* AI reply draft is queued in your dashboard Approvals tab!
```

### Node 5: Backend Callback (Manual Optimization Party Trick)
- **Type**: `n8n-nodes-base.httpRequest`
- **Method**: `POST`
- **URL**: `http://localhost:8000/api/webhooks/simulate` (or your ngrok URL)
- **Body**:
```json
{
  "campaign_id": "{{ $('Webhook Trigger').item.json.campaign_id }}",
  "event_type": "meeting_booked",
  "contact_id": "{{ $('Webhook Trigger').item.json.contact_id }}"
}
```

---

## 1-Click Import into n8n

1. In your n8n workspace, click **Workflows** → **Import from File...**
2. Select [`n8n/graph8_self_healing_relay.json`](file:///e:/revops-graph8-hackathon/n8n/graph8_self_healing_relay.json).
3. Under **Credentials**, add your `graph8 API Key` and Slack/Discord webhook.
4. Toggle workflow to **Active**.
