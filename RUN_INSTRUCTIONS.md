# Step-by-Step Run Instructions — graph8 Self-Healing Outbound Agent

Follow this guide to get the entire system running locally from zero in under 3 minutes.

---

## 1. Prerequisites

- **Python 3.10+** (Python 3.13 tested)
- **Node.js 18+** & **npm**
- (Optional for external webhooks) **ngrok** or **Cloudflare Tunnel**

---

## 2. Environment Configuration (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` (or project root `.env`):

```bash
cp backend/.env.example backend/.env
```

### Environment Variables Glossary

| Variable | Default Value | Description |
|---|---|---|
| `GRAPH8_API_KEY` | `your_graph8_api_key_here` | API key from graph8 Settings → API with the 24 required scopes. |
| `GRAPH8_BASE_URL` | `https://be.graph8.com/api/v1` | Verified base REST endpoint for graph8 platform. |
| `GRAPH8_WEBHOOK_SECRET` | `mock_webhook_secret_graph8` | Secret used for HMAC-SHA256 signature verification. |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible endpoint (Groq by default for ultra-low latency). |
| `LLM_API_KEY` | `your_groq_api_key_here` | Groq / OpenAI API key. |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | High-accuracy model for variant generation & sentiment analysis. |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Optional Supabase project URL (SQLite fallback active if omitted). |
| `SUPABASE_KEY` | `your_supabase_key` | Supabase service_role or anon key. |
| `WEBHOOK_BASE_URL` | `http://localhost:8000` | Public URL (ngrok) for receiving graph8 webhooks live. |
| `SIMULATION_MODE` | `true` | When `true`, enables sandbox offline mode so demo runs even without live keys. |
| `VOICE_ESCALATION_ENABLED` | `false` | Stretch feature flag for voice triggers. |
| `PORT` | `8000` | Backend API server port. |

---

## 3. Database Setup (Supabase / Postgres)

### Option A: Automatic Local SQLite (Zero-Config, Instant)
No setup required! If `SUPABASE_URL` is omitted or contains placeholder text, the application automatically boots on an internal SQLite database (`backend/graph8_agent.db`) pre-seeded with winning reference email templates.

### Option B: Supabase (Postgres)
1. In your [Supabase Dashboard](https://supabase.com/dashboard), navigate to **SQL Editor**.
2. Click **New Query**, copy the contents of [`backend/schema.sql`](file:///e:/revops-graph8-hackathon/backend/schema.sql), and click **Run**.
3. Copy your project URL and service role key into `backend/.env`.

---

## 4. Running the Backend

In your terminal:
```powershell
python backend/run_backend.py
```
- The backend starts on `http://localhost:8000`.
- Interactive Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

---

## 5. Running the Frontend Dashboard

In a second terminal:
```powershell
npm.cmd --prefix frontend run dev
```
- The dashboard starts on `http://localhost:5173`.
- Open `http://localhost:5173` in your browser.
- Real-Time SSE Indicator will display: **"Real-Time SSE Stream Active"** with a green pulse.

---

## 6. How to Connect a Gmail / SMTP Mailbox in graph8

1. In your browser, log in to your graph8 workspace at [app.graph8.com](https://app.graph8.com).
2. Go to **Settings** → **Mailboxes** → Click **New Mailbox** (or **New SMTP Mailbox**).
3. If using Gmail, generate a **16-digit Google App Password**:
   - Go to your Google Account: [myaccount.google.com/security](https://myaccount.google.com/security)
   - Enable **2-Step Verification** (if not already enabled).
   - Search for **App passwords** (or go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
   - Name it `graph8 Mailbox` and click **Create**.
   - Copy the 16-character code (e.g. `abcd efgh ijkl mnop`).
4. Fill out the **New SMTP Mailbox** modal in graph8:
   - **From Name**: Your Name or Company Name (e.g. `Alex from GrowthOps`)
   - **From Email**: `your-email@gmail.com`
   - **SMTP Host**: `smtp.gmail.com`
   - **SMTP Port**: `587` (TLS) or `465` (SSL)
   - **SMTP Username**: `your-email@gmail.com`
   - **SMTP Password**: Paste your 16-digit App Password (without spaces)
   - **IMAP Host**: `imap.gmail.com`
   - **IMAP Port**: `993`
   - **IMAP Username**: `your-email@gmail.com`
   - **IMAP Password**: Paste your 16-digit App Password
   - **Daily Limit**: `50` (recommended starting limit)
   - **Enable Warmup**: Check the box ✅
5. Click **Save / Test Connection**.
6. In your local agent dashboard, navigate to **Settings** (or **Overview**). Your connected mailbox will show **"Active ✅"**.

---

## 7. Public Webhook Setup (ngrok + graph8 Webhooks)

### Step 1: Start ngrok
In a separate terminal:
```bash
ngrok http 8000
```
Copy the Forwarding HTTPS URL provided by ngrok (e.g. `https://xyz-1234.ngrok-free.app`).

### Step 2: Create Webhook in graph8
1. In graph8, go to **Settings** → **Webhooks** → Click **Create Webhook**.
2. **Name**: `Self Healing Agent`
3. **URL**: `https://xyz-1234.ngrok-free.app/api/webhooks/graph8`
4. **Events Checkmarks (Select these exact checkboxes)**:
   - **Email**:
     - [x] **Email Sent**
     - [x] **Email Opened**
     - [x] **Email Clicked**
     - [x] **Email Replied** *(Vital: triggers AI sentiment & inbox draft)*
     - [x] **Email Bounced**
     - [x] **Email Unsubscribed**
   - **Campaign**:
     - [x] **Campaign Launched**
     - [x] **Campaign Paused**
     - [x] **Campaign Completed**
   - **Sequence**:
     - [x] **Sequence Started**
     - [x] **Sequence Finished**
   - **Contact**:
     - [x] **Contact Added**
     - [x] **Contact Updated**
   - **Intent**:
     - [x] **Intent Surged**
     - [x] **Intent Threshold Met**
5. **Note on GRAPH8_WEBHOOK_SECRET**:
   - graph8 does not generate or require a webhook secret in this modal.
   - The backend receiver automatically detects this and accepts graph8 events securely without requiring a secret.
6. Click **Save / Create Webhook**.

---

## 8. 60-Second Demo Walkthrough for Judges

1. Open `http://localhost:5173`.
2. Click **"Launch Campaign"** → Enter ICP:
   - Campaign Name: `Fintech Series B Expansion`
   - Industry: `Financial Technology & Payments`
   - Titles: `VP Sales, Head of Revenue Operations, CRO`
3. Click **"Launch & Auto-Enrich"**:
   - Watch the **Live Decision Ticker** update in real-time as the agent discovers high-intent prospects and generates Variant A (Pain Point) & Variant B (ROI Metrics).
4. Go to **HITL Approvals** (Page 7) → Click **"1-Click Approve"** for the first-send gate.
5. Click **"Demo Webhook Simulator"** in the top header:
   - Click **"Auto-Trigger Loop ⚡"** (dispatches 5 sends on Variant A and Variant B, plus a positive reply).
6. Go to **Campaign Detail** (Page 3):
   - Notice Variant A was evaluated as underperforming.
   - The agent automatically generated a **Kill Variant** decision, reallocated traffic to winning Variant B, and formulated Variant C.
7. Go to **AI Inbox** (Page 5):
   - Notice the inbound reply with **"🔥 Positive"** sentiment.
   - Click **"Generate AI Draft"** to watch the LLM formulate an instant calendar reply.
   - Review and submit to Approvals.
