# Graph8 — Autonomous Self-Healing Outbound Engine
## Closed-Loop Agentic RevOps Powered by Graph8, LangGraph & Groq LLM

> **An enterprise-grade, closed-loop outbound revenue operations agent that dynamically discovers buyer intent from Graph8, synthesizes contrasting A/B pitch variants, enforces daily pacing with mathematical balancing, ingests real-time webhook telemetry, and executes an automated Bayesian reinforcement cycle to scale winning pitch angles autonomously.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-StateGraph-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![React: 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev)

---

### 🌐 Live Production Deployments
- **Live Frontend Dashboard**: [https://frontend-graph8.vercel.app/](https://frontend-graph8.vercel.app/)
- **Live Backend API**: [https://graph8-hackathon.onrender.com](https://graph8-hackathon.onrender.com)
- **Live Health Endpoint**: [https://graph8-hackathon.onrender.com/api/health](https://graph8-hackathon.onrender.com/api/health)
- **Live Graph8 Webhook Receiver**: `https://graph8-hackathon.onrender.com/api/webhooks/graph8`
- **Interactive API Documentation (Swagger)**: [https://graph8-hackathon.onrender.com/docs](https://graph8-hackathon.onrender.com/docs)
- **Instant Demo Login**: `demo@graph8.ai` / `password123` (or click **"1-Click Instant Demo Login"** on the `/login` screen)

---

## 1. Executive Summary & Problem Solved

### The Outbound RevOps Crisis
Traditional cold outbound tools (e.g., Lemlist, Apollo, Instantly) are **static and brittle**:
- Sales Development Reps (SDRs) load thousands of prospects into a static sequence and blast the exact same copy.
- When an angle fatigues, generates high bounces, or receives hostile replies, human operators only notice weeks later after thousands of accounts and secondary domains have already been burned.
- Human review is either **absent** (uncontrolled spam) or an **operational bottleneck** (manually triaging every reply).

### The Graph8 Self-Healing Solution
Our agent replaces static sequences with an **adaptive, closed-loop reinforcement engine**:
1. **Dynamic Intent Discovery**: Programmatically pulls high-intent accounts and verified decision-makers from Graph8's real-time buyer intent signal engine and CRM.
2. **Two-Tier Cohort & Pacing Architecture**:
   - **Total Target Cohort**: Fetches and enriches the full cohort (e.g. 25, 50, 100 prospects) upfront and persists them in SQLite with campaign relational links.
   - **Daily Pacing Limit**: Controls automated sequence enrollment (e.g. 7, 25, 50 contacts/day) to safeguard domain deliverability.
3. **Exact Proportional Allocation (No Skew)**: Deterministic allocation guarantees that daily quotas are split with mathematical precision (e.g., 7 sends = 4 Variant A + 3 Variant B; across 14 sends = exactly 7 Variant A + 7 Variant B).
4. **Closed-Loop Bayesian Self-Healing (LangGraph)**:
   - Computes Bayesian Laplace-smoothed scores across opens, replies, and sentiment.
   - Automatically reallocates 100% of future traffic to the Champion variant if an underperformer diverges.
   - Synthesizes an evolutionary **Variant C (Mutant)** combining the winning angle with social proof contrast to challenge the champion.
5. **Human-in-the-Loop (HITL) Governance**: High-impact actions (first sends, variant copy changes, and prospect replies) pause in an auditable Governance Queue. If the human reviewer rejects copy, the agent captures feedback and iterates new variants until approved.
6. **Unified Dual Mailbox & Smart Inbox**: Real incoming replies trigger Groq LLM sentiment classification (`positive`, `neutral`, `negative`), generate an intelligent AI response draft, and broadcast over Server-Sent Events (SSE) to the dashboard.

---

## 2. System Architecture

```
                                  ┌────────────────────────────┐
                                  │   Graph8 Cloud Platform    │
                                  │ • Intent Signals & Keywords│
                                  │ • Contacts & Enrichment API│
                                  │ • Sequencer Engine (Steps) │
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
│  │ with Cloudflare UA)│      │ MemorySaver     │     │ GPT-OSS-120B      │  │
│  └────────────────────┘      └────────┬────────┘     └───────────────────┘  │
│                                       │                                     │
│                ┌──────────────────────┴──────────────────────┐              │
│                │                                             │              │
│                ▼                                             ▼              │
│     ┌──────────────────────┐                     ┌────────────────────────┐ │
│     │ HITL Approval Gates  │                     │ Server-Sent Events     │ │
│     │ (Review & Clearance) │                     │ (SSE Real-Time Stream) │ │
│     └──────────┬───────────┘                     └───────────┬────────────┘ │
│                │ (Approved / Rejected Loop)                  │              │
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
│ • inbox_messages • settings     │           │ • 4. Smart Inbox • 9. Ref Copy│
│ • mailbox_settings              │           │ • 5. Webhook Simulator        │
└─────────────────────────────────┘           └───────────────────────────────┘
```

---

## 3. LangGraph Cyclical State Machine

```
[Campaign Launch] ──> (1. signal_node) ──> Fetches & stores full cohort (e.g. 50 prospects)
                             │
                             ▼
                     (2. enrichment_node) ──> Parallel enrichment of tech stack, funding & LinkedIn
                             │
                             ▼
                (3. variant_generator_node) ──> Synthesizes Variant A & Variant B from Reference Copy
                             │
                             ▼
                  [ HITL GATE 1: Clearance ] ──> Halts until Human reviews & approves copies
                             │
             ┌───────────────┴────────────────┐
             ▼ (If Rejected)                  ▼ (If Approved)
    [Iterate with Feedback]        (4. scheduler / executor)
    [Generate Fresh Variants]                 │
             │                                ▼ Enrolls Day 1 Batch (e.g. 7 prospects: 4 A / 3 B)
             └──────────────────────> [Graph8 Sequencer] 
                                              │
                                              ▼
                                    [ Webhook Telemetry ] ──> Ingests opens, replies, sentiment
                                              │
                                              ▼
                                      (5. feedback_node)
                                              │
                                              ▼
                                (6. performance_evaluator_node) ──> Calculates Bayesian conversion score
                                              │
                                              ▼
                                     (7. reallocation_node) ──> Scales Winner to 100% / Queues Kill
                                              │
                                              ▼
                                (8. evolution_generator_node) ──> Synthesizes Variant C from Champion DNA
                                              │
                                              ▼
                                 (9. voice_escalation_node) ──> Escalates hottest intent (Score >= 90)
```

---

## 4. Graph8 API Key Permissions (Required Scopes)

When generating your API key in **Graph8** (`Settings -> API -> Create API Key`), ensure the following scopes are enabled:

| Category | Recommended Scopes | Operational Requirement |
| :--- | :--- | :--- |
| **Campaigns** | `campaigns:read`, `campaigns:write`, `campaigns:run`, `campaigns:launch` | Programmatic campaign initialization and lifecycle state transitions. |
| **Contacts** | `contacts:read`, `contacts:write` | Fetching real CRM contacts, saving discovered prospects, and audience syncing. |
| **Sequences** | `sequences:read`, `sequences:write`, `sequences:run` | Creating sequencers, attaching email steps with A/B copy, and daily enrollment. |
| **Enrichment** | `enrichment:read`, `enrichment:write`, `enrichment:run` | Retrieving verified emails, company size, tech stack, and LinkedIn profiles. |
| **Intent** | `intent:read`, `intent:write` | Pulling intent keywords and buyer velocity signals. |
| **Analytics** | `analytics:read` | Telemetry queries for open rates, deliverability, and bounce tracking. |
| **Webhooks** | `webhooks:read`, `webhooks:run` | Managing and subscribing webhook endpoints. |
| **Companies** | `companies:read`, `companies:write` | Firmographic intelligence lookups. |
| **Search** | `search:read`, `search:run` | Querying target ICP decision makers. |
| **Lists** | `lists:read`, `lists:write` | Audience list segmentation. |
| **Account** | `account:read` | Account profile verification. |

---

## 5. Live Webhook Setup Guide

In the **Graph8 Dashboard** (`Settings -> Webhooks -> Create Webhook`):
1. **Name**: `Graph8-Self-Healing-Agent`
2. **URL**: `https://graph8-hackathon.onrender.com/api/webhooks/graph8`
3. **Events Selected**:
   - `campaign.created`, `campaign.launched`, `campaign.paused`, `campaign.completed`, `campaign.status_changed`
   - `sequence.draft_created`, `sequence.started`, `sequence.paused`, `sequence.completed`, `contact.enrolled`, `step.completed`, `step.failed`
   - `email.sent`, `email.replied`, `email.bounced`, `email.link_clicked`, `contact.unsubscribed`
   - `meeting.booked`, `meeting.cancelled`
   - `company.enriched`, `enrichment_job.completed`
   - `audience.ready`, `intelligence.completed`
4. **Secret**: Copy the webhook signing secret into `GRAPH8_WEBHOOK_SECRET` in your `.env`.

---

## 6. How to Run Locally in 1-Click

### Quickstart (Windows & Linux/Mac):
```bash
# Windows (1-Click runner starts backend on 8000 and frontend on 5173):
run_dev.bat

# Cross-platform Python runner:
python run_dev.py
```

### Manual Setup:

#### Backend:
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 7. Automated Test Suite

Run the full pytest suite with end-to-end LangGraph reinforcement validation:
```bash
cd backend
pytest
```
*Output: 5 passed in tests/test_agent_flow.py and tests/test_auth.py with 100% test coverage.*

---

## 8. Hackathon Evaluator Walkthrough

1. **Login**: Go to [https://frontend-graph8.vercel.app/](https://frontend-graph8.vercel.app/) and click **"1-Click Instant Demo Login"**.
2. **Review Pre-Seeded Campaign**: Inspect the active campaign *"Fintech & SaaS RevOps Outbound (Live Agent)"* with Champion Variant A (Score: 8.6) and Challenger Variant B (Score: 6.2).
3. **Enriched Prospects**: Click the **Prospects** tab. Click any prospect to open the **Graph8 Enriched Prospect Modal** (verified emails, tech stack tags, direct LinkedIn links, and campaign relation).
4. **Smart Inbox**: Click the **Inbox** tab to view live inbound replies with sentiment analysis and auto-generated AI draft responses ready to send in 1 click.
5. **Interactive Webhook Simulator**: Click the **"Simulator"** button in the top navigation bar to dispatch a live simulated email open, reply, or booked meeting to see the dashboard metrics, SSE pulses, and self-healing agent decisions react in real-time.
6. **Judge Showcase**: Click the **"🏆 Judge Showcase"** button in the header to view the competitor comparison matrix, the 5 agentic superpowers, and the 2-minute executive pitch.
