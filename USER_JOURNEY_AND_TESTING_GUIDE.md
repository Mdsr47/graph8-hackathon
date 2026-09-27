# Graph8 Self-Healing Autonomous RevOps Outbound Agent
## Production Architecture, User Journey & Evaluation Guide

This guide provides an end-to-end overview of the **Autonomous Self-Healing RevOps Outbound Agent** powered by **Graph8**, **LangGraph**, **Groq LLM**, and **FastAPI / React**.

---

## 1. System Architecture & Live Deployment

The system is deployed in a production decoupling architecture:
- **Frontend (UI & Dashboard)**: Hosted on Vercel at `https://graph8-hackathon-1.vercel.app` (or your designated Vercel domain). Configured with automatic edge proxy rewrites to eliminate CORS and route `/api/*` directly to Render.
- **Backend (Agent & Engine)**: Hosted on Render at `https://graph8-hackathon.onrender.com`. Runs 24/7 on an asynchronous Python 3.12 container running FastAPI, SQLite database, LangGraph state engine, and an automated background scheduler.
- **Webhooks**: Live receiver configured at `https://graph8-hackathon.onrender.com/api/webhooks/graph8`.

```
┌─────────────────────────────────┐
│     Graph8 Outbound Engine      │
│  (Contacts, Campaigns, Events)  │
└────────────────┬────────────────┘
                 │ (1) Real-time Webhook Events: email.sent, email.replied, meeting.booked
                 ▼
┌────────────────────────────────────────────────────────┐
│             FastAPI Backend (Render Live)              │
│  - Webhook Ingestion & HMAC Verification               │
│  - Groq LLM Sentiment Classifier & Auto-Drafting      │
│  - LangGraph Self-Healing Bayesian State Machine       │
│  - Proportional Pacing Daily Sequencer                 │
│  - SQLite Database & Real-Time SSE Broadcaster        │
└───────────────▲────────────────────────▲───────────────┘
                │                        │
         (2) API Proxy             (3) Live UI Sync
                │                        │
┌───────────────┴────────────────────────┴───────────────┐
│             React + Tailwind Dashboard (Vercel)        │
│  - Instant 1-Click Demo Login                          │
│  - Campaigns & ICP Filter Builder                      │
│  - Human-in-the-Loop (HITL) Governance Queue           │
│  - Real-time Prospects & Enriched Intelligence Drawer  │
│  - Inbound AI Smart Inbox & Meeting Tracker            │
│  - Champion vs Challenger Variant Analytics            │
└────────────────────────────────────────────────────────┘
```

---

## 2. Graph8 API Key Permissions (Required Scopes)

When creating your API Key inside the **Graph8 Dashboard** (`Settings -> API -> Create API Key`), select the following recommended scopes to enable complete autonomous outbound operation:

### Essential Scopes to Check:
| Category | Recommended Scopes | Purpose |
| :--- | :--- | :--- |
| **Campaigns** | `campaigns:read`, `campaigns:write`, `campaigns:launch`, `campaigns:run` | Programmatically creating and launching outbound campaigns from the agent. |
| **Contacts** | `contacts:read`, `contacts:write` | Fetching real CRM contacts, saving discovered prospects, and syncing audience tags. |
| **Sequences** | `sequences:read`, `sequences:write`, `sequences:run` | Generating sequencers, configuring email steps with A/B variants, and enrolling daily batches. |
| **Enrichment** | `enrichment:read`, `enrichment:write`, `enrichment:run` | Pulling verified emails, company revenue, tech stack, and LinkedIn profiles. |
| **Intent** | `intent:read`, `intent:write` | Discovering high-intent visitor accounts and tracking buying keywords. |
| **Analytics** | `analytics:read` | Ingesting delivery, open, reply, and click rates. |
| **Webhooks** | `webhooks:read`, `webhooks:run` | Subscribing and managing event delivery pipelines. |
| **Companies** | `companies:read`, `companies:write` | Reading firmographic intelligence (funding, company size, industry). |
| **Search** | `search:read`, `search:run` | Executing ICP filter searches across the contact database. |
| **Lists** | `lists:read`, `lists:write` | Managing contact groups and target cohorts. |
| **Account** | `account:read` | Verifying account connectivity and workspace info. |

> **Note**: Scopes like *Ads*, *Voice*, *Quotes*, *Deals*, *Marketplace*, and *Signatures* can remain unchecked or default unless you require extended integrations.

---

## 3. Graph8 Webhook Configuration

In the **Graph8 Dashboard** (`Settings -> Webhooks -> Create Webhook`):
1. **Name**: `Graph8-Self-Healing-Agent` (or any custom name)
2. **URL**: `https://graph8-hackathon.onrender.com/api/webhooks/graph8`
3. **Events Selected**:
   - **Campaign**: `campaign.created`, `campaign.updated`, `campaign.launched`, `campaign.paused`, `campaign.completed`, `campaign.status_changed`
   - **Sequence**: `sequence.draft_created`, `sequence.started`, `sequence.paused`, `sequence.completed`, `contact.enrolled`, `step.completed`, `step.failed`
   - **Engagement**: `email.sent`, `email.replied`, `email.bounced`, `email.link_clicked`, `contact.unsubscribed`
   - **Meetings**: `meeting.booked`, `meeting.cancelled`
   - **Enrichment**: `company.enriched`, `enrichment_job.completed`
   - **Intelligence / Audience**: `audience.ready`, `intelligence.completed`
4. **Secret**: Copy the generated Signing Secret and place it in your backend environment as `GRAPH8_WEBHOOK_SECRET`.

---

## 4. End-to-End User Journey

### Step 1: Instant Zero-Friction Authentication
- Navigate to the frontend login page.
- Click **"1-Click Instant Demo Login"** (or use `demo@graph8.ai` / `password123`).
- The system authenticates against SQLite and returns a session bearer token with full access.

### Step 2: Campaign Setup & ICP Definition
- Open the **Campaigns** tab and click **"+ New Campaign"**.
- Enter target ICP parameters:
  - Industry (e.g., `Fintech & Enterprise SaaS`)
  - Target Job Titles (e.g., `VP of Sales`, `Head of RevOps`, `CRO`)
  - Target Contacts Limit (e.g., `25`)
  - Daily Pacing Limit (e.g., `7 contacts / day`)
- Select reference email styles to guide the tone of the generated variants.
- Click **"Launch Campaign"**.

### Step 3: Discovery, Real Enrichment & Modal Inspection
- The agent executes `signal_node` and `enrichment_node`:
  - Pulls real contacts from Graph8 CRM (such as Barry Peraino, Julie Sharp, David Young) and intent discovery pools.
  - Enriches each contact with tech stack, LinkedIn URL, funding stage, and buying intent score (0-100).
- Open the **Prospects** tab:
  - Click on any prospect row to open the **Graph8 Enriched Prospect Modal**.
  - Review verified email, direct LinkedIn link, associated Campaign ID, and detected tech stack.

### Step 4: Human-in-the-Loop (HITL) Governance Loop
- The agent generates two contrasting email copy angles using Groq LLM:
  - **Variant A**: Pain-point & deliverability angle.
  - **Variant B**: ROI & benchmark metric angle.
- The campaign enters a protective hold state until human approval.
- Open the **Approvals** tab:
  - **If Approved**:
    - The agent automatically registers the campaign and sequence in Graph8 via the real API.
    - Adds the email copy steps into the sequencer.
    - Automatically enforces daily limit pacing (e.g., exactly 7 prospects today: 4 allocated to Variant A, 3 to Variant B).
    - Dispatches the first batch and logs the audit trail in Agent Decisions.
  - **If Rejected**:
    - The user provides rejection feedback (e.g., *"Make it shorter, less salesy, more peer-to-peer"*).
    - The agent immediately iterates and generates 2 fresh variants matching the reviewer's instructions.
    - Loops until the user is satisfied and gives approval.

### Step 5: Real-Time Webhook Processing & Smart Inbox
- As contacts engage, Graph8 fires webhooks to `/api/webhooks/graph8`:
  - **Email Sent**: Increments sends count and updates daily pacing.
  - **Email Opened**: Increments variant open counter.
  - **Email Replied**:
    - Groq LLM performs real-time sentiment analysis (`positive`, `neutral`, `negative`).
    - Generates an intelligent AI draft response tailored to the lead's company and message.
    - Saves into the `inbox_messages` database table and broadcasts via Server-Sent Events (SSE).
    - The **Inbox** tab immediately displays the unread reply with a 1-click **"Send AI Draft"** button.
  - **Meeting Booked**: Marks contact status as `meeting_booked` and increments meeting conversion metrics.

### Step 6: Closed-Loop Bayesian Self-Healing (LangGraph)
- Telemetry from webhooks re-enters LangGraph at `feedback_node`.
- `performance_evaluator_node` calculates Bayesian confidence-smoothed conversion scores:
  $$\text{Score} = \frac{(0.15 \cdot \text{OpenRate} + 0.35 \cdot \text{ReplyRate} + 0.50 \cdot \text{PositiveReplyRate}) \cdot N + 3 \cdot 0.05}{N + 3}$$
- If a variant significantly underperforms (loser score $\le 40\%$ of winner with $\ge 5$ sends):
  1. The agent automatically shifts 100% of future traffic to the Champion.
  2. Generates a `kill_variant` proposal in the Governance Queue.
  3. Synthesizes an evolutionary mutant **Variant C** combining winning hooks with new angles.
  4. Resumes testing in a balanced tournament.

---

## 5. Local Development Commands

To run both backend and frontend locally in 1 click:
```bash
# Windows 1-Click Runner
run_dev.bat

# Or via Python
python run_dev.py
```
- **Backend**: Runs on `http://localhost:8000`
- **Frontend**: Runs on `http://localhost:5173`
- **API Documentation**: Available at `http://localhost:8000/docs`

---

## 6. Verification Checklist for Hackathon Evaluators

- [x] **Zero CORS Friction**: Vercel edge proxies `/api/*` to Render seamlessly.
- [x] **Pre-Seeded Demo Data**: Includes active campaign, variants, enriched prospects, decision history, and inbound inbox replies with AI draft responses.
- [x] **Instant Login**: Click "1-Click Instant Demo Login" on `/login` without typing credentials.
- [x] **Live Graph8 Integration**: Verified connection to `https://be.graph8.com/api/v1` for campaigns, contacts, sequences, intent, and webhooks.
- [x] **Real-Time Telemetry**: Real webhooks and the in-app "Simulate Webhook Event" modal update the dashboard instantly via Server-Sent Events (SSE).
- [x] **Pacing Safety**: Strict mathematical quota allocation prevents domain burning.
