# graph8 Self-Healing Outbound Agent — User Journey & Capabilities Guide

> **Document**: `USER_JOURNEY_AND_CAPABILITIES.md`  
> **Platform**: graph8 Autonomous Self-Healing Outbound Engine  
> **Tech Stack**: LangGraph + Groq LLM (Llama-3.3-70B) + FastAPI + SQLite Relational DB + React 18 / Tailwind  

---

## 1. System Overview — Problem This System Solves

Traditional cold email tools (Instantly, Lemlist, Apollo) blast static sequences. When a pitch angle fatigues, generates high bounces, or receives hostile replies, a human SDR must manually notice weeks later after domain reputation has already been degraded.

The **graph8 Self-Healing Outbound Agent** closes this loop autonomously:
1. **Dynamic Intent Discovery**: Ingests real-time buyer intent signals from Graph8 to find accounts actively researching solutions.
2. **Double-Tier Prospect Management**:
   - Fetches and enriches the **entire target cohort** (e.g., 50, 100, 200 prospects) at once so users see all leads immediately.
   - Enforces a **daily sending limit** (e.g., 7, 25, 50/day) to prevent mailbox burn and maintain deliverability.
3. **Exact Proportional Variant Split**: Distributes sends to active variants with mathematical precision (no random hash skew). For a daily limit of 7, exactly 4 go to Variant A and 3 go to Variant B; across 14 sends, exactly 7 and 7.
4. **15-Day Reinforcement Tournament**:
   - **Phase 1 (Days 1–15)**: 50/50 exploration to establish statistically significant conversion baselines.
   - **Day 15 Milestone**: Computes Bayesian Laplace-smoothed conversion scores. The **Champion is scaled to 80% traffic**, the loser is throttled/retired, and the LLM synthesizes an evolutionary **Variant C (20% traffic)** to launch Phase 2.
5. **Human-in-the-Loop (HITL) Governance**: High-impact actions (first sends, copy changes, variant termination, and prospect replies) pause for 1-click human clearance.
6. **Unified Dual Mailbox**: Supports native Graph8 sequences alongside direct local SMTP/IMAP credentials.

---

## 2. Complete End-to-End User Journey (Step-by-Step)

```
[ Step 1: Connect Settings (Graph8 API & SMTP/IMAP) ]
                       │
                       ▼
[ Step 2: Seed / Select Reference Email Copies ]
                       │
                       ▼
[ Step 3: Create Campaign (Total Cohort vs Daily Pacing) ]
                       │
                       ▼
[ Step 4: Review Prospects Tab (Filtered by Campaign ID & Paginated) ]
                       │
                       ▼
[ Step 5: HITL Approvals Queue (Inspect Full Subjects & Bodies, Edit, Approve) ]
                       │
                       ▼
[ Step 6: Automated Daily Scheduler Dispatches Batch (e.g., 4 Var A + 3 Var B) ]
                       │
                       ▼
[ Step 7: Inbound Webhooks Stream Delivery & Sentiment Telemetry ]
                       │
                       ▼
[ Step 8: Monitor Dedicated Variant Analytics Dashboard ]
                       │
                       ▼
[ Step 9: 15-Day Milestone Evaluated: Scale Champion (80%), Evolve Variant C (20%) ]
                       │
                       ▼
[ Step 10: Triage Unified Inbox, Approve AI Drafted Replies, Voice Escalation ]
```

---

### Step 1: Connecting Mailbox & API Credentials
- Navigate to **Settings** (`/settings`):
  - **Graph8 API Key**: Connect your key with checked permissions (`campaigns`, `webhooks`, `contacts`, `intent`).
  - **Mailbox Configuration**: Enter your custom SMTP (host, port, user, app password) and IMAP credentials.
  - The system tests authentication and establishes secure connectivity for live dispatch and inbox fetching.

---

### Step 2: Seed & Select Reference Emails (The Agent's Knowledge Base)
- Navigate to **Reference Emails** (`/reference-emails`):
  - Add your highest-converting cold email copy, value propositions, and style notes.
  - The default database comes pre-seeded with proven B2B templates (pain-point hook & metric-driven proof).
  - When launching a new campaign, you can select which specific reference emails the LLM should emulate.

---

### Step 3: Launching a Campaign with Distinct Cohort & Pacing Limits
- Navigate to **Campaigns** (`/campaigns`) and click **"New Campaign"**:
  - Fill in Campaign Name, Target Industry, Persona Titles, and Intent Keywords.
  - **Input 1 — Total Prospects to Fetch & Enrich**: (e.g. `23` or `100`). Defines how many prospects are identified from Graph8 and stored permanently in SQLite.
  - **Input 2 — Daily Campaign Send Pacing Limit**: (e.g. `7` or `25`/day). Defines the batch size dispatched to sequence daily.
- Click **"Launch Campaign"**:
  - The LangGraph initial pipeline runs (`signal_node` -> `enrichment_node` -> `variant_generator_node`).
  - **Crucial Safety Rule**: The workflow stops at `variant_generator_node` and creates a pending approval gate. **No emails are dispatched until you approve the copy!**

---

### Step 4: Exploring Prospects with Campaign Filtering & Pagination
- Navigate to **Prospects** (`/prospects`):
  - All requested prospects (e.g., 23) appear immediately with enriched corporate emails, verified badges, tech stack, and LinkedIn profiles.
  - Every row displays a distinct badge with its **Campaign Name & ID**.
  - Use the **Campaign Dropdown Filter** to isolate leads for a specific campaign.
  - Use the **Pagination Bar** (10, 15, 25, 50 rows per page, Next/Previous) to browse large cohorts smoothly.

---

### Step 5: Human-in-the-Loop Governance (Review Full Copy & Approve)
- Navigate to **Approvals** (`/approvals`):
  - A pending card **"First Send Clearance: A/B Pitch Variants"** awaits review.
  - Click **"Review & Approve"** to open the modal:
    - **Side-by-Side View**: Both **Variant A** (Pain-Point Angle) and **Variant B** (ROI Metric Angle) display their full subject lines and complete email body templates.
    - **Live Editing**: You can modify subject lines, adjust value propositions, or tweak personalization merge tags (`{name}`, `{company}`, `{title}`).
    - Character counts and template hints update in real time.
  - Click **"Approve & Activate"**:
    - Your edited copies are saved directly to SQLite.
    - The first daily batch (e.g., 7 prospects) is dispatched into the active sequence!

---

### Step 6: Daily Batch Pacing & Exact Proportional Allocation
- The system enforces strict daily sending quotas:
  - If daily limit is 7: exactly 7 contacts are enrolled on Day 1.
  - The remaining 16 contacts stay in status `new` awaiting Day 2.
- **Deterministic Proportional Balancing**:
  - Out of 7 contacts, exactly **4 go to Variant A** and **3 go to Variant B**.
  - On Day 2, the balancer routes **3 to Variant A** and **4 to Variant B**.
  - Total across 14 sends: **7 Variant A and 7 Variant B** (strict 50/50 balance without statistical skew).
- **Background Scheduler & Manual Trigger**:
  - An automated scheduler checks every day at midnight UTC / 24-hour interval and pushes the next batch.
  - On the campaign card, you can also click **"Push Next Daily Batch Now"** to manually force-dispatch the next cohort anytime.

---

### Step 7: Real-Time Webhook Telemetry & Sentiment Classification
- As prospects interact with emails:
  - Events stream in via the Graph8 webhook endpoint (`/api/webhooks/graph8`).
  - The agent logs each event (`sent`, `opened`, `replied`, `bounced`, `meeting_booked`) and links it to the contact and variant.
  - For inbound replies, the Groq LLM analyzes the text:
    - **Positive** 🔥: Interested, requests demo or pricing.
    - **Neutral**: General inquiry, asks for more info.
    - **Negative / Objection**: "Not interested", "Unsubscribe", or timing friction.
  - Telemetry is broadcast live over Server-Sent Events (SSE) to update the dashboard without page refreshes.

---

### Step 8: Dedicated Variant Analytics Dashboard
- Navigate to **Variant Analytics** (`/analytics` from sidebar):
  - **KPI Cards**: Real-time Outbound Sent, Deliverability Rate, Open Rate, Reply Rate, Positive Reply Rate, Bounces, and Booked Meetings.
  - **Head-to-Head Comparison Cards**: Variant A vs. Variant B comparing Bayesian scores, traffic allocation, deliverability, and expandable full email body previews.
  - **Intent Distribution**: Visual tier breakdown of hot (90+), warm (80-89), and mild accounts.

---

### Step 9: 15-Day Reinforcement Tournament & Variant C Evolution
- The engine operates in automated 15-day optimization cycles:
  - **Days 1–15 (Cycle 1: Exploration)**: 50% Variant A / 50% Variant B.
  - **Day 15 Evaluation Milestone**:
    - The agent evaluates Bayesian Laplace conversion scores:
      $$\text{Score} = \frac{(0.15 \times \text{OpenRate} + 0.35 \times \text{ReplyRate} + 0.50 \times \text{PositiveRate}) \times N + 3 \times 0.05}{N + 3}$$
    - The winning variant is crowned **Champion and scaled to 80% traffic**.
    - The losing variant is throttled to 0-20% or retired.
    - The LangGraph `evolution_generator_node` runs: takes the Champion's winning subject and body copy, incorporates observed buyer replies, and synthesizes **Variant C (The Challenger)**.
  - **Days 16–30 (Cycle 2: Tournament)**:
    - Champion (80% traffic) competes with Challenger Variant C (20% traffic) for the next 15 days.
  - **Live Demo Trigger**: You can click **"⚡ Evaluate 15-Day Milestone Now"** directly on the Analytics page or campaign card to simulate the Day 15 milestone instantly for judges!

---

### Step 10: Unified Inbox, AI Contextual Replies, & Voice Escalation
- Navigate to **Inbox** (`/inbox`):
  - Inbound messages appear categorized by sentiment.
  - The agent analyzes the email thread and drafts a personalized reply (e.g. sharing calendar link or addressing objections).
  - Drafts can be edited and approved with 1 click before sending.
- **Voice Escalation**: For ultra-high-intent accounts (score >= 90), the agent flags the account for voice call follow-up.
