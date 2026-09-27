# graph8 Self-Healing Outbound Agent — Architecture & Workflow Deep-Dive

> **Document**: `ARCHITECTURE_AND_WORKFLOW_EXPLAINED.md`  
> **Audience**: Engineering Team, Hackathon Judges, and System Architects  
> **Core Concepts**: LangGraph Cyclical StateGraph, Bayesian Reinforcement, Graph8 REST API, Webhook Ingestion, Proportional Balancer, 15-Day Tournament Cycles  

---

## 1. Architectural Blueprint & Data Flow

The **graph8 Self-Healing Outbound Agent** is engineered as a stateful, closed-loop control system. Unlike standard linear scripts or static sequencers, it continuously consumes feedback signals, calculates statistical conversion probabilities, and mutates its operational parameters autonomously.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FULL DATA LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────────────────┘

  [Graph8 Cloud] ─────── Intent Signals (Keywords) ─────────┐
                                                            ▼
                                                   [1. signal_node]
                                                            │ (Stores Cohort in DB)
                                                            ▼
                                                  [2. enrichment_node]
                                                            │ (Parallel Async Enriches)
                                                            ▼
  [Reference Emails] ── Few-Shot Exemplars ─────> [3. variant_generator_node]
                                                            │ (Synthesizes Var A & B)
                                                            ▼
                                                ┌───────────────────────┐
                                                │   HITL GATE 1         │
                                                │   Human Clearance     │
                                                │   (Subjects & Bodies) │
                                                └───────────┬───────────┘
                                                            │ (Approved by Human)
                                                            ▼
                                              [4. scheduler_service / executor]
                                                            │ (Enforces Daily Pacing: e.g. 7)
                                                            │ (Proportional Balancer: 4 A / 3 B)
                                                            ▼
                                                   [Graph8 Sequences]
                                                            │
                                                            ▼
                                                   [Prospects Inboxes]
                                                            │
                                                     (Opens / Replies)
                                                            │
                                                            ▼
                                                [Graph8 Webhooks Engine]
                                                            │ (HMAC Signature Verified)
                                                            ▼
                                                    [5. feedback_node]
                                                            │
                                                            ▼
                                              [6. performance_evaluator_node]
                                                            │ (Bayesian Laplace Score)
                                                            ▼
                                                   [7. reallocation_node]
                                                            │
                                    ┌───────────────────────┴───────────────────────┐
                                    │ (Day 15 Milestone Reached)                    │ (High Intent >= 90)
                                    ▼                                               ▼
                     [8. evolution_generator_node]                      [9. voice_escalation_node]
                     • Champion Scaled to 80%                           • Voice Call Clearance Gate
                     • Loser Throttled to 0-20%
                     • Breeds Variant C (20%)
                     • Advances to Cycle 2 (Days 16-30)
```

---

## 2. LangGraph Node-by-Node Technical Specification

The core agent workflow is implemented in [`backend/app/agent/workflow.py`](file:///e:/revops-graph8-hackathon/backend/app/agent/workflow.py) using LangGraph's `StateGraph`.

### Node 1: `signal_node` (Intent Account Discovery)
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: Programmatically pulls target prospects matching the campaign's Ideal Customer Profile (ICP).
- **Execution Logic**:
  1. Inspects `campaign.target_contacts_limit` (e.g. 23, 50, 100).
  2. Queries Graph8 Intent API via `graph8_client.list_intent_keywords(page=1, limit=10)`.
  3. Queries Graph8 Contacts API via `graph8_client.get_contacts_for_keyword(keyword_id, limit=target_limit)`.
  4. Stores the **entire cohort** into the SQLite `contacts` table with `status="new"`, `current_step=1`, and links `campaign_id`.
  5. Logs an `agent_decision` record and emits a Server-Sent Event (`contacts_discovered`).

### Node 2: `enrichment_node` (Concurrent Async Enrichment)
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: Appends corporate intelligence (verified emails, tech stack, funding rounds, LinkedIn URLs) to every prospect.
- **Execution Logic**:
  1. Executes concurrently using `asyncio.gather(*[_enrich_contact(c) for c in contacts])`.
  2. Calls `graph8_client.enrich_person(email)` with a strict 3.0s timeout and instant structured fallback.
  3. Writes enriched JSON metadata directly to `contacts.enriched_data`.

### Node 3: `variant_generator_node` (Contrasting Copy Synthesis)
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: Generates 2 contrasting cold email pitches (A/B testing) using Groq LLM (Llama-3.3-70B).
- **Prompt Strategy**:
  - Ingests the campaign's selected reference emails (`reference_email_ids`).
  - Instructs the LLM to synthesize:
    - **Variant A**: Focuses on curiosity, pain-point agitation, and low-friction discovery.
    - **Variant B**: Focuses on concrete ROI metrics, benchmark proof, and quantifiable outcomes.
  - Inserts both rows into the `variants` table with `allocation_percentage=50.0`.
  - **The Safety Halt**: Creates a pending approval gate in `approvals` (`type="send_new_variant"`).
  - The workflow edge terminates at `END` here. **No emails are dispatched until a human operator clears the copy in the Governance Queue.**

### Node 4: `executor_node` & `scheduler_service` (Daily Pacing & Proportional Balancing)
- **File**: `backend/app/services/scheduler_service.py` & `backend/app/agent/nodes.py`
- **Purpose**: Enforces daily sending batch limits and routes prospects to variants with mathematical precision.
- **Why This Matters**:
  - If a user sets 23 total prospects and 7/day limit, blasting all 23 immediately burns domain reputation.
  - The scheduler enrolls **exactly 7 prospects today**, leaving 16 prospects in status `new` for future days.
- **The Exact Proportional Balancing Algorithm**:
  - Previous implementations used `(i * 37) % 100` (hash modulo), which resulted in severe statistical skew (e.g. 15 to Variant B and 6 to Variant A out of 21).
  - We replaced this with a **Deterministic Cumulative Deficit Balancer**:
    $$\text{Deficit}_v = (\text{Total Assigned} + 1) \times \text{Target Proportion}_v - \text{Current Assigned}_v$$
    For each prospect in the batch, the agent routes to the variant with the largest deficit.
  - **Batch of 7 (50/50 split)**:
    - Prospect 1 $\to$ Variant A (A=1, B=0)
    - Prospect 2 $\to$ Variant B (A=1, B=1)
    - Prospect 3 $\to$ Variant A (A=2, B=1)
    - Prospect 4 $\to$ Variant B (A=2, B=2)
    - Prospect 5 $\to$ Variant A (A=3, B=2)
    - Prospect 6 $\to$ Variant B (A=3, B=3)
    - Prospect 7 $\to$ Variant A (A=4, B=3) $\implies$ **Exactly 4 to Variant A, 3 to Variant B**.
  - **Day 2 Batch of 7**:
    - Continues with cumulative counts (A=4, B=3):
    - Prospect 8 $\to$ Variant B (A=4, B=4)
    - Prospect 9 $\to$ Variant A (A=5, B=4)
    - ...
    - Prospect 14 $\to$ Variant B (A=7, B=7) $\implies$ **Across 14 sends: exactly 7 to Variant A, 7 to Variant B**.

### Node 5: `feedback_node` (Webhook Telemetry Ingestion)
- **File**: `backend/app/routers/webhooks.py` & `backend/app/agent/nodes.py`
- **Purpose**: Ingests incoming events from Graph8 webhooks (`email.sent`, `email.opened`, `email.replied`, `email.bounced`, `meeting_booked`).
- **Execution Logic**:
  1. Validates `X-Graph8-Signature` HMAC.
  2. Resolves `contact_id` and `variant_id`.
  3. For inbound replies: calls `llm_client.classify_sentiment(reply_text)` to categorize as `positive`, `neutral`, or `negative`.
  4. Increments metrics on the specific variant in the `variants` table (`opens_count`, `replies_count`, `positive_replies_count`, `bounces_count`).
  5. Inserts an event record in `events` and re-enters the LangGraph cycle at `feedback_node`.

### Node 6: `performance_evaluator_node` (Bayesian Conversion Scoring)
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: Computes robust, statistically smoothed conversion scores for each active variant.
- **Mathematical Formula**:
  $$\text{Raw Composite} = (0.15 \times \text{OpenRate}) + (0.35 \times \text{ReplyRate}) + (0.50 \times \text{PositiveReplyRate})$$
  $$\text{Bayesian Score} = \frac{\text{Raw Composite} \times N + (k \times \text{PriorRate})}{N + k}$$
  - $N$: Total sends for the variant.
  - $k = 3.0$: Laplace prior weight (pseudo-counts).
  - $\text{PriorRate} = 0.05$: Expected 5% baseline conversion rate.
- **Why Bayesian Laplace Smoothing?**
  - Prevents wild fluctuations on small cohorts (e.g. 1 lucky reply out of 2 sends would otherwise report 50% conversion).
  - Requires statistical volume before declaring a variant superior.

### Node 7: `reallocation_node` & 15-Day Milestone Evaluator
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: Executes the self-healing tournament transition.
- **15-Day Optimization Cycle Rules**:
  - **Days 1–15 (Cycle 1: Exploration)**: Both variants receive 50% traffic to establish baselines.
  - **Day 15 Milestone**:
    1. Evaluator ranks variants by Bayesian score and positive replies.
    2. The highest-scoring variant is crowned **Champion** and scaled to **80% traffic allocation**.
    3. The underperforming variant is throttled to 0% (retired).
    4. Triggers `evolution_generator_node` to breed **Variant C (The Challenger)** with 20% traffic allocation.
    5. Advances campaign to **Cycle 2 (Days 16–30)**.

### Node 8: `evolution_generator_node` (LLM Challenger Breeding)
- **File**: `backend/app/agent/nodes.py` & `backend/app/llm/llm_client.py`
- **Purpose**: Synthesizes Variant C by learning from the winning hooks of the Champion variant.
- **Execution Logic**:
  - Ingests the Champion's subject and body copy.
  - Ingests buyer replies and objections.
  - Instructs Groq LLM: *"Retain the proven hook of the winning email, but test an evolved social proof angle and tighter call-to-action."*
  - Inserts Variant C into the database and launches Cycle 2 head-to-head testing!

### Node 9: `voice_escalation_node` (High-Intent Hot Lead Escalation)
- **File**: `backend/app/agent/nodes.py`
- **Purpose**: For accounts where buyer intent score reaches $\ge 90$ or inbound sentiment indicates immediate buying urgency, the agent creates a `voice_escalation` gate in Approvals, enabling 1-click AI outbound calling via Graph8's voice API.

---

## 3. Database Schema & Relational Design

The system runs on SQLite with async connectivity (`aiosqlite`) and foreign key indexing:

### 1. `campaigns` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (PK) | Unique UUID |
| `name` | TEXT | Campaign display name |
| `status` | TEXT | `active`, `paused`, `completed` |
| `daily_limit` | INTEGER | Pacing quota (e.g. 7, 25/day) |
| `target_contacts_limit` | INTEGER | Total cohort size (e.g. 23, 100) |
| `sent_today` | INTEGER | Sends executed during current 24h window |
| `last_batch_run_at` | TEXT | ISO timestamp of last batch run |
| `cycle_number` | INTEGER | Current 15-day tournament cycle (1, 2, 3...) |
| `cycle_start_date` | TEXT | Timestamp when current cycle began |
| `cycle_duration_days` | INTEGER | Duration of cycle (default: 15) |
| `champion_variant_id` | TEXT | ID of winning champion variant |
| `challenger_variant_id` | TEXT | ID of evolved challenger variant |

### 2. `variants` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (PK) | Variant UUID |
| `campaign_id` | TEXT (FK) | Relational link to campaign |
| `subject` | TEXT | Cold email subject line |
| `body_template` | TEXT | Full template with personalization merge tags |
| `status` | TEXT | `active`, `retired`, `killed`, `draft` |
| `sends_count` | INTEGER | Total outbound contacts enrolled |
| `opens_count` | INTEGER | Confirmed opens |
| `replies_count` | INTEGER | Inbound replies |
| `positive_replies_count` | INTEGER | Replies classified as positive interest |
| `bounces_count` | INTEGER | Hard/soft bounces |
| `score` | REAL | Bayesian smoothed conversion score |
| `allocation_percentage` | REAL | Traffic weight (e.g. 50.0, 80.0, 20.0) |

### 3. `contacts` Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (PK) | Contact UUID |
| `campaign_id` | TEXT (FK) | Indexed relational link (`idx_contacts_campaign`) |
| `name` | TEXT | Full prospect name |
| `email` | TEXT | Verified corporate email |
| `title` | TEXT | Job title |
| `company` | TEXT | Account name |
| `intent_score` | INTEGER | Graph8 Intent Score (0–100) |
| `status` | TEXT | `new`, `enrolled`, `replied`, `bounced` |
| `enriched_data` | TEXT (JSON) | LinkedIn, tech stack, funding metadata |

---

## 4. Addressing Common Telemetry & Pacing Questions

### Q1: "Why did my analytics show sends when Graph8 SMTP/webhooks were not yet connected?"
- When a batch is approved, the agent pushes the prospects to Graph8's sequence engine (`graph8_client.add_contacts_to_sequence`).
- In SQLite, the agent increments `sends_count` (Outbound Dispatched).
- Email deliverability is calculated as:
  $$\text{Deliverability} = \max(0, \text{sends} - \text{bounces})$$
- If no bounces have occurred and webhooks have not yet reported back, deliverability displays as 100% of dispatched sequence leads. Once live webhooks are connected (or simulated via `/api/webhooks/simulate`), delivery receipts, opens, and sentiment events update in real time.

### Q2: "Why did 21 sends appear previously when I selected 7/day limit?"
- In the initial iteration, the workflow executed `executor_node` during initiation before human review, the approval handler executed another batch, and the unconstrained scheduler loop triggered a third batch within 60 seconds (7 + 7 + 7 = 21).
- **The Permanent Fix**:
  1. The initiation workflow now halts strictly at `variant_generator_node` $\to$ `END`. No contacts are enrolled before human approval.
  2. `scheduler_service.process_daily_batch` enforces `sent_today < daily_limit`. Once 7 contacts are sent, the quota is locked until the next 24-hour cycle.
  3. `last_batch_run_at` is persisted, preventing recurring execution within the same daily window.

### Q3: "Why did Variant B get 15 sends and Variant A get 6 sends out of 21?"
- Previous code used `(i * 37) % 100` (hash modulo), which consistently assigned 5 out of 7 contacts to Variant B across three successive runs ($5 \times 3 = 15$ vs $2 \times 3 = 6$).
- **The Permanent Fix**:
  - Replaced with the **Deterministic Cumulative Deficit Balancer**.
  - Tracks running sends across variants: routes prospect 1 to A, 2 to B, 3 to A, 4 to B, 5 to A, 6 to B, 7 to A $\implies$ **Exactly 4 to Variant A and 3 to Variant B**.
  - On Day 2, it balances to 3 to A and 4 to B $\implies$ **14 sends = exactly 7 to A and 7 to B**.

---

## 5. Judge Presentation Script & Hackathon Cheat-Sheet

### 2-Minute Elevator Pitch:
> *"Judges, current outbound tools are static spray-and-pray engines. SDRs load a list, blast the same copy, and burn domain reputation when an angle fatigues. We built the **graph8 Self-Healing Outbound Agent**. It takes buyer intent signals from Graph8, enriches decision-makers, and writes two contrasting pitch angles. It strictly paces daily sends with exact proportional balance to safeguard email reputation. But here is the breakthrough: every 15 days, our Bayesian reinforcement evaluator identifies the winning Champion, scales it to 80% traffic, and uses Groq Llama-3.3-70B to breed an evolutionary Variant C from the winner's DNA. It is a completely autonomous, self-healing outbound engine with executive Human-in-the-Loop governance."*

### Key Features to Demonstrate to Judges:
1. **Campaign Creation**: Show the two distinct inputs: Total Cohort (e.g. 23) vs Daily Send Pacing (e.g. 7/day).
2. **Prospects Tab**: Show the 23 enriched contacts with Campaign Name/ID badges and smooth pagination.
3. **Approvals Tab**: Show the side-by-side modal displaying full email bodies for Variant A and B, live character counts, and 1-click edit-and-approve.
4. **Variant Analytics Tab**: Show the 15-day tournament progress bar and click **"⚡ Evaluate 15-Day Milestone Now"** to witness the AI scale the champion to 80% and breed Variant C live!
5. **Decisions Tab**: Show the complete, auditable log of autonomous agent reasoning.
