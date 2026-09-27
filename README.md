# graph8 — Autonomous Self-Healing Outbound Engine

> **An enterprise-grade, closed-loop outbound revenue operations agent powered by Graph8, LangGraph, Groq LLM (Llama-3.3-70B), FastAPI, and React 18. Dynamically discovers buyer intent, synthesizes contrasting A/B pitch variants, enforces daily pacing with mathematical balancing, ingests real-time webhook telemetry, and executes a 15-day Bayesian reinforcement tournament to scale winning pitch angles autonomously.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![React: 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev)

---

## 1. Executive Summary & Problem Solved

### The Outbound RevOps Crisis
Traditional outbound systems (e.g., Lemlist, Apollo, Instantly) are **static and brittle**:
- Sales Development Reps (SDRs) load 1,000 prospects into a static sequence and spray-and-pray the same copy.
- When an angle fatigues, burns domain deliverability, or generates negative sentiment, human operators only notice weeks later after thousands of accounts have been burned.
- Human review is either **absent** (uncontrolled spam) or an **operational bottleneck** (manually triaging every reply).

### The graph8 Self-Healing Outbound Solution
Our agent replaces static sequences with an **adaptive, closed-loop reinforcement engine**:
1. **Dynamic Intent Discovery**: Programmatically pulls high-intent accounts and verified decision-makers from Graph8's buyer intent signal engine.
2. **Two-Tier Cohort & Pacing Architecture**:
   - **Total Prospects to Fetch**: Immediately pulls and enriches the full cohort (e.g. 50, 100, 200 prospects) and persists them in SQLite with campaign relational links.
   - **Daily Pacing Limit**: Controls automated sequence enrollment (e.g. 7, 25, 50 contacts/day) to safeguard domain reputation.
3. **Exact Proportional Allocation (No Skew)**: Deterministic allocation guarantees that daily quotas are split with mathematical precision (e.g. 7 sends = 4 Variant A + 3 Variant B; next day = 3 Variant A + 4 Variant B).
4. **15-Day Reinforcement Tournament**:
   - **Phase 1 (Days 1–15)**: 50/50 exploratory tournament to gather statistically significant baseline telemetry.
   - **Day 15 Milestone**: Computes Bayesian Laplace-smoothed scores across opens, replies, and sentiment. Crowns the **Champion (scaled to 80% traffic)**, throttles/retires the underperformer, and uses LLM few-shot synthesis to breed an evolutionary **Variant C (20% traffic)**.
   - **Phase 2 (Days 16–30)**: Tournament between Champion and Variant C.
5. **Strict Human-in-the-Loop (HITL) Governance**: First sends, variant copy edits, and reply drafts are held in an auditable Governance Queue before execution.
6. **Dual Mailbox Architecture**: Seamlessly supports Graph8 native sequences alongside local direct SMTP/IMAP credentials for unified inbox reading and drafting.

---

## 2. System Architecture

```
                                  ┌────────────────────────────┐
                                  │   graph8 Cloud Platform    │
                                  │ • Intent Signals & Keywords│
                                  │ • Search & Enrichment API  │
                                  │ • Sequence Engine (Sends)  │
                                  │ • Real-Time Webhook Stream │
                                  └──────────────┬─────────────┘
                                                 │
                                 Webhooks (HMAC) / REST API
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend & LangGraph Agent Engine                 │
│                                                                             │
│  ┌────────────────────┐      ┌─────────────────┐     ┌───────────────────┐  │
│  │ Graph8Client       │ ───> │ LangGraph State │ <── │ LLMClient (Groq)  │  │
│  │ (Verified Endpoints│      │ Cyclical Graph  │     │ Llama-3.3-70B     │  │
│  └────────────────────┘      └────────┬────────┘     └───────────────────┘  │
│                                       │                                     │
│                ┌──────────────────────┴──────────────────────┐              │
│                │                                             │              │
│                ▼                                             ▼              │
│     ┌──────────────────────┐                     ┌────────────────────────┐ │
│     │ HITL Approval Gates  │                     │ Server-Sent Events     │ │
│     │ (Review & Clearance) │                     │ (SSE Real-Time Stream) │ │
│     └──────────┬───────────┘                     └───────────┬────────────┘ │
│                │                                             │              │
│                ▼                                             │              │
│     ┌──────────────────────┐                                 │              │
│     │ Daily Scheduler &    │                                 │              │
│     │ Proportional Balancer│                                 │              │
│     └──────────┬───────────┘                                 │              │
└────────────────┼─────────────────────────────────────────────┼──────────────┘
                 │                                             │
                 ▼                                             ▼
┌─────────────────────────────────┐           ┌───────────────────────────────┐
│     SQLite Relational Engine    │           │  React 18 + Tailwind Dashboard│
│ • campaigns      • events       │           │ • 1. Overview  • 6. Analytics │
│ • contacts       • decisions    │           │ • 2. Campaigns • 7. Decisions │
│ • variants       • approvals    │           │ • 3. Prospects • 8. Approvals │
│ • reference_emails              │           │ • 4. Inbox     • 9. Ref Copy  │
│ • mailbox_settings              │           │ • 5. Replies   • 10. Settings │
└─────────────────────────────────┘           └───────────────────────────────┘
```

---

## 3. LangGraph Cyclical Workflow

```
[Start Campaign] ──> (1. signal_node) ──> Fetches & stores full cohort (e.g. 50)
                            │
                            ▼
                    (2. enrichment_node) ──> Concurrently enriches tech stack, funding, LinkedIn
                            │
                            ▼
               (3. variant_generator_node) ──> Synthesizes Variant A & Variant B
                            │
                            ▼
                 [ HITL GATE 1: Clearance ] ──> Halts until Human reviews & approves copies
                            │
                            ▼ (Upon Human Approval)
                (4. scheduler / executor) ──> Enrolls Day 1 Batch (e.g. 7 prospects: 4 A / 3 B)
                            │
                            ▼
                  [ Webhook Telemetry ] ──> Ingests opens, replies, sentiment, bounces
                            │
                            ▼
                    (5. feedback_node)
                            │
                            ▼
              (6. performance_evaluator_node) ──> Computes Bayesian Laplace conversion score
                            │
                            ▼
                   (7. reallocation_node) ──> Scales Champion to 80% / Retires Loser
                            │
                            ▼
              (8. evolution_generator_node) ──> Synthesizes Variant C from Champion DNA
                            │
                            ▼
               (9. voice_escalation_node) ──> Escalates hottest intent (Score >= 90)
```

---

## 4. Key Capabilities & Feature Matrix

| Capability | Static Outbound Tools | graph8 Self-Healing Agent |
| :--- | :--- | :--- |
| **Audience Discovery** | Manual CSV upload | Programmatic Graph8 Intent Keywords |
| **Prospect Pacing** | All-at-once blast | Cohort Store + Strict Daily Batch Pacing |
| **A/B Split Balancing** | Random hash (skewed) | Exact Proportional Deficit Balancing |
| **Optimization Loop** | Manual operator guesswork | 15-Day Bayesian Tournament (80% Winner / 20% Variant C) |
| **Inbound Triage** | SDR inbox clutter | Groq LLM Sentiment Classification & Contextual Reply Drafting |
| **Governance & Safety** | None or rigid | HITL Approval Gates with live copy editing |
| **Analytics** | Simple aggregate opens | Per-variant comparative telemetry, score progression, & intent distribution |

---

## 5. How to Clone and Run

### Prerequisites
- **Python**: 3.11, 3.12, or 3.13
- **Node.js**: v18 or v20+ and npm
- **Git**
- **Groq API Key** (Free tier available at [console.groq.com](https://console.groq.com))
- **Graph8 API Key** (From Graph8 dashboard settings)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Mdsr47/graph8-hackathon.git
cd graph8-hackathon
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` in the root and in `backend/`:
```bash
# Create .env from template
cp .env.example .env
```
Fill in your credentials:
```ini
GRAPH8_API_KEY=your_graph8_api_key_here
GRAPH8_BASE_URL=https://api.graph8.ai/v1
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite+aiosqlite:///backend/graph8_agent.db
ENVIRONMENT=production
PORT=8000
```

### Step 3: Setup Backend
```bash
cd backend
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### Step 4: Setup Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Start the Full Stack Application

**Terminal 1 — Backend (Port 8000):**
```bash
# From workspace root
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend (Port 5173):**
```bash
cd frontend
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 6. One-Click Database Reset & Clean Testing

To reset all test records and start with a pristine database at any point:
```bash
python reset_database.py
```
This script wipes historical contacts, events, approvals, and decisions, re-seeds winning reference email templates, and notifies the live frontend to refresh automatically via Server-Sent Events (SSE).

---

## 7. Running Unit & Integration Tests

Execute the comprehensive test suite verifying the database defaults, Graph8 endpoints, Groq LLM generation, and the end-to-end LangGraph agent cycle:
```bash
python -m pytest backend/tests/test_agent_flow.py -v
```

---

## 8. Webhook Configuration (Graph8)

To stream real-time events from Graph8 into your local agent:
1. In Graph8 Dashboard, navigate to **Webhooks** -> **Create Webhook**.
2. **URL**: `https://your-ngrok-subdomain.ngrok-free.app/api/webhooks/graph8`
3. Select Events:
   - `campaign.launched`
   - `campaign.paused`
   - `campaign.completed`
   - `email.sent`
   - `email.opened`
   - `email.replied`
   - `email.bounced`
4. Save the webhook. Incoming events will immediately trigger sentiment classification and Bayesian score updates in your dashboard.

---

## 9. Hackathon Judges & Architecture Highlights

1. **Autonomous Self-Healing Reinforcement**: It does not just observe outbound stats; it programmatically makes decisions, reallocates sending volume to the top performer (80%), and breeds mutant challenger copy (Variant C) via LLM.
2. **Strict Daily Pacing & Deterministic Proportionality**: Solves the real-world deliverability bottleneck by ensuring daily batch limits are never exceeded and variant splits are strictly maintained without statistical skew.
3. **Enterprise Human-in-the-Loop Governance**: Balances autonomous speed with executive oversight—ensuring no untested copy is blasted without human clearance.
4. **Bayesian Statistical Rigor**: Employs Laplace smoothing with prior pseudo-counts ($k=3.0$) to avoid premature optimization on small sample sizes.
