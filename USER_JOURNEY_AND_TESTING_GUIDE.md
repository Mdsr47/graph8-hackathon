# graph8 Self-Healing Outbound Agent — User Journey & Complete Guide

Yeh guide complete system ko samajhnay, test karnay, graph8 API keys/webhooks configure karnay, aor SQLite database refresh karnay ke liye step-by-step banayi gayi hai.

---

## 1. Complete User Journey (Kiya Kiya Kar Sakty Hain?)

System ek **Autonomous Revenue Operations (RevOps) Engine** hai jo outbound campaigns ko real-time data ki bunyaad par self-heal karta hai. Yahan complete user flow hai:

```
[1. ICP & Reference Picker] ──► [2. Discovery & 50-Batch Pacing] ──► [3. A/B Variant Gen]
                                                                             │
[6. Evolved Variant C] ◄── [5. Auto-Reallocation & Kill Gate] ◄── [4. First-Send HITL Gate]
         │                                                                   │
   (50/50 Split) ◄───────────────────────────────────────────────────────────┘
         │
[7. AI Inbox & Smart Reply] ──► [8. Live Decision & SSE Telemetry]
```

### Step 1: Campaign Launch & Style Selection
- Dashboard par **"Campaigns"** page par jayen aur **"+ New Campaign"** click karein.
- **ICP Targetting Details** enter karein:
  - *Campaign Name* (e.g., `Fintech Founders Outbound`)
  - *Industry* (e.g., `B2B SaaS / Fintech`)
  - *Target Titles* (e.g., `VP Sales, Head of RevOps, CRO`)
  - *Company Size* (e.g., `50-500 employees`)
- **Reference-Email Style Picker**:
  - Modal mein available winning reference emails show hon gi (e.g. *Cold Outbound — SaaS Pain Point*, *Executive Hook — ROI & Case Study*).
  - Jo specific email styles pasand hon unke checkmarks select karein. LLM inhi selected styles ke tone aur hook structure ko follow kar ke variants generate karega. Agar koi select na karein tou general high-converting tone use hogi.
- **Daily Send Pacing Limit**:
  - Warmup safety ke liye default **50 sends/day** set hai (custom limit bhi enter kar sakty hain). Yeh domain reputation ko protect karta hai aur account ko ban honay se bachata hai.

### Step 2: Autonomous Contact Discovery (Limit 50 Batch)
- Jab campaign launch hoti hai, agent LangGraph ka `signal_node` aur `enrichment_node` trigger karta hai.
- graph8 platform se intent keywords aur companies search ki jaati hain (max 50 prospects per batch limit).
- System har prospect ko enrich karta hai: email verification status, tech stack, funding rounds, aur intent score.

### Step 3: A/B Variant Generation
- Agent do contrasting email copy angles generate karta hai:
  - **Variant A**: Pain-point & problem-centric copy.
  - **Variant B**: ROI & metric-driven value proposition copy.
- Both variants ko baseline **50% / 50% traffic allocation** assign hota hai.

### Step 4: Human-in-the-Loop Gate #1 (First Send Clearance)
- **Safety First**: Agent direct prospect ko email nahi bhejta jab tak human approve na karay.
- **"Approvals"** tab par ek card appear hoga: *"Approve First Send of New A/B Variants"*.
- User subjects aur content review karta hai aur **"Approve & Execute"** click karta hai.
- Approving ke baad sequence initiate hoti hai aur daily pacing limit (e.g., 50/day) ke hisaab se sends start hotay hain.

### Step 5: Self-Healing Reinforcement Loop (Bayesian Evaluator)
- Jaise hi prospect emails open karte hain, reply karte hain, ya positive meeting request aati hai, graph8 webhooks backend par hit hotay hain.
- **Bayesian Confidence Smoothing**:
  Agent raw counts ko dekh kar jaldbaazi mein decision nahi leta (taake 1 send par 100% reply false positive na ban jaye).
  Formula:
  $$\text{Score} = \frac{(0.15 \times \text{OpenRate} + 0.35 \times \text{ReplyRate} + 0.50 \times \text{PosReplyRate}) \times N + 3 \times 0.05}{N + 3}$$
- **Threshold Rule**:
  Jab dono variants ke pass minimum sample size ($N \ge 5$ sends) ho aur loser variant ka score leader ke muqablay mein $\le 40\%$ ho (with $\ge 1$ positive reply difference), tou agent us loser variant ko **underperformer** declare karta hai.
- **Automated Traffic Reallocation**:
  Future traffic un-enrolled prospects ke liye foran **100% winner** ko divert ho jaati hai (loser ka allocation 0% ho jata hai).
- **HITL Gate #2 (Kill Approval)**:
  Approvals queue mein *"Approve Self-Healing Variant Kill & Reallocation"* card add hota hai jis mein statistical reasoning detailed hoti hai.

### Step 6: Evolutionary Variant C (The Mutant Challenger)
- Loser variant kill hotay hi, LangGraph ka `evolution_generator_node` winner variant ke winning angles aur user ke selected reference email styles ko blend kar ke **Variant C** generate karta hai.
- **HITL Gate #3 (Variant C Approval & Direct Editing)**:
  Modal open kar ke user Variant C ka subject aur body template directly edit kar sakta hai aur approve kar sakta hai.
  Approve hotay hi traffic Winner aur Variant C ke darmiyan **50/50 exploratory split** par distribute ho jaati hai.

### Step 7: AI Unified Inbox & Smart Reply
- Jab koi prospect reply karta hai, Groq LLM uske sentiment ko classify karta hai:
  - **Positive** (Green badge: demo/meeting request)
  - **Neutral** (Yellow badge: info request, out of office)
  - **Negative** (Red badge: unsubscribe, not interested)
- User **"AI Inbox"** page par ja kar positive replies ke samnay **"Generate AI Draft"** click kar sakta hai.
- LLM foran meeting booking link ke sath personalized reply draft tayyar karta hai.
- User **"Send via graph8 Mailbox"** click karta hai jo directly graph8 connected mailbox ke zarye prospect ko deliver ho jata hai.

### Step 8: Real-Time SSE Stream & Audit Trail
- Browser refresh kiye baghair har action live synchronize hota hai:
  - **Live Decision Ticker**: Agent ke dimagh ke har decision ki reasoning aur state change.
  - **Live Event Log**: Opens, replies, bounces, sentiment scores.
  - **Approvals Badge**: Unreviewed items ka counter real-time update hota hai.

---

## 2. graph8 API Key Scopes Checklist (140 Scopes Mein Se Kon Say Check Karne Hain?)

graph8 ke **Settings → API Keys → Create Key** mein 140 scopes ki list aati hai. Hackathon agent ke full automation ke liye niche diye gaye **exact checkmarks** tick karein:

### Category 1: Campaigns (Full Access)
- [x] `campaigns:read` (Campaigns list aur stats dekhne ke liye)
- [x] `campaigns:write` (Campaign create karne ke liye)
- [x] `campaigns:update` (Campaign metadata update karne ke liye)
- [x] `campaigns:delete` (Optional)
- [x] `campaigns:launch` (Campaign start karne ke liye)
- [x] `campaigns:pause` (Campaign pause karne ke liye)

### Category 2: Contacts / Leads (Full Access)
- [x] `contacts:read` (Contacts list aur details retrieve karne ke liye)
- [x] `contacts:write` (New contacts add karne ke liye)
- [x] `contacts:update` (Contact status aur tags change karne ke liye)
- [x] `contacts:delete` (Optional)
- [x] `contacts:enrich` (Email verification aur company info fetch karne ke liye)

### Category 3: Sequences (Full Access)
- [x] `sequences:read` (Sequences view karne ke liye)
- [x] `sequences:write` (Email sequences create karne ke liye)
- [x] `sequences:enroll` (Prospects ko sequence steps mein enroll karne ke liye)
- [x] `sequences:pause` (Underperforming steps pause karne ke liye)

### Category 4: Inbox & Email Messages (Full Access)
- [x] `inbox:read` (Inbound emails aur prospect replies read karne ke liye)
- [x] `inbox:reply` (AI-drafted replies directly send karne ke liye)
- [x] `inbox:tag` (Replied, Interested, Meeting tags set karne ke liye)
- [x] `emails:send` (Direct email delivery ke liye)

### Category 5: Intent & Signals (Full Access)
- [x] `intent:read` (B2B intent keywords aur company surge signals fetch karne ke liye)
- [x] `intent:keywords:read` (Keywords list dekhne ke liye)
- [x] `intent:companies:read` (High intent companies dekhne ke liye)

### Category 6: Search & Discovery
- [x] `search:contacts` (ICP criteria ke mutabiq leads dhoondne ke liye)
- [x] `search:companies` (Matching companies search karne ke liye)

### Category 7: Mailboxes
- [x] `mailboxes:read` (Connected Gmail/SMTP status check karne ke liye)
- [x] `mailboxes:write` (Mailbox warmup aur limits sync karne ke liye)

### Category 8: Webhooks
- [x] `webhooks:read` (Registered webhooks inspect karne ke liye)
- [x] `webhooks:write` (Agent ka public webhook URL bind karne ke liye)

### Category 9: Analytics & Reporting
- [x] `analytics:read` (Open rate, reply rate, bounce telemetry lene ke liye)

*(Tip: Agar wahan "Select All" ya "Full Admin Access" ka option ho tou wo bhi select kar sakty hain).*

---

## 3. graph8 Webhook Events Checklist (70+ Events Mein Se Kon Say Check Karne Hain?)

Jab aap **Settings → Webhooks → Create Webhook** par click karein:
- **Name**: `Self Healing Agent`
- **URL**: `https://<your-ngrok-subdomain>.ngrok-free.app/api/webhooks/graph8`
- **Secret**: graph8 webhook modal mein secret ki zaroorat nahi hoti; backend automatic without secret bhi accept karta hai.

Niche diye gaye **exact events** par checkmark lagayen:

### Email Events (Most Important ⭐)
- [x] **Email Sent** (Telemetry aur daily pacing counter ke liye)
- [x] **Email Opened** (Open rate metrics ke liye)
- [x] **Email Clicked** (Engagement telemetry ke liye)
- [x] **Email Replied** (*Most Critical*: AI sentiment analysis aur instant reply draft trigger karta hai)
- [x] **Email Bounced** (Lead health aur reputation protection ke liye)
- [x] **Email Unsubscribed** (Compliance aur sequence removal ke liye)

### Campaign Events
- [x] **Campaign Launched**
- [x] **Campaign Paused**
- [x] **Campaign Completed**
- [x] **Campaign Updated**

### Sequence Events
- [x] **Sequence Started**
- [x] **Sequence Completed**
- [x] **Sequence Step Transitioned**

### Contact Events
- [x] **Contact Added**
- [x] **Contact Updated**
- [x] **Contact Tagged**

### Intent Signals Events
- [x] **Intent Surged** (Jab koi target company buying signals show karay)
- [x] **Intent Threshold Met** (Voice escalation aur high-priority outbound trigger)

---

## 4. Database Reset (Purana Record Delete Kar Ke Fresh Shuru Karna)

Aap ne mention kiya tha ke SQLite DB open kar ke delete karnay ke bawajood frontend par purana data nazar aata hai aur locks ka issue aa sakta hai. Isko solve karne ke liye humne dedicated **1-Command Database Reset Script** bana di hai:

### Step 1: Script Run Karein
Terminal mein project root se yeh command run karein:
```powershell
python backend/reset_database.py
```

### Kiya Hoga?
1. Yeh script `backend/graph8_agent.db` ke tamam test records (campaigns, contacts, variants, decisions, approvals, events) ko safe transaction mein empty kar deti hai.
2. Default winning **Reference Emails** ko fresh restore kar deti hai.
3. Database file ko `VACUUM` kar ke lock release kar deti hai.
4. Terminal par `Database reset successfully! Fresh state ready.` print hota hai.

### Step 2: Frontend Refresh
- Browser mein `http://localhost:5173` refresh karein.
- Tamam counters 0 par hon gay aur fresh testing ke liye clean state mil jaye gi.

---

## 5. End-to-End Testing Procedure (Step-by-Step Test Kaise Karein?)

### Method A: Frontend UI Se Test Karna
1. Backend start karein: `python backend/run_backend.py`
2. Frontend start karein: `npm.cmd --prefix frontend run dev`
3. Browser mein `http://localhost:5173` open karein.
4. **Campaign Launch**:
   - `Campaigns` par jayen → `+ New Campaign` click karein.
   - Name: `Fintech US Expansion`
   - Select reference style checkbox.
   - Daily Limit: `50`.
   - `Launch & Auto-Enrich` click karein.
5. **Approve First Send**:
   - `Approvals` page par jayen.
   - Variant A & B ka card show hoga → `Approve & Execute` click karein.
6. **Simulate Reinforcement Loop**:
   - Top right header mein **"Demo Webhook Simulator"** button par click karein.
   - **"Auto-Trigger Loop ⚡"** click karein.
   - Yeh automatically Variant A aur Variant B ke liye 5 sends inject karega, aur Variant B ko 1 positive reply dega.
7. **Verify Self-Healing**:
   - `Campaigns` → Click `Fintech US Expansion`.
   - Dekhein: Variant B ka score barh gaya hai ($0.125$) aur Variant A ($0.019$) underperforming mark ho gaya hai.
   - Traffic foran Variant B ko **100%** assign ho chuki hai.
   - `Approvals` tab par jayen:
     - Card #1: *Approve Self-Healing Variant Kill & Reallocation* (Loser ko terminate karne ke liye).
     - Card #2: *Approve Evolved Variant C (Mutant Challenger)* (Naye evolved variant ko approve karne ke liye, subject/body editable hai).

### Method B: Automated Pytest Suite Se Test Karna
System mein built-in automated test suite maujood hai jo backend, database, LLM, graph8 endpoints, aur cyclical LangGraph loop ko verify karta hai:
```powershell
python -m pytest backend/tests/test_agent_flow.py -v
```
Yeh 4 tests automatically run karta hai:
1. `test_database_and_defaults`: Database initialization aur reference templates verification.
2. `test_graph8_client_endpoints`: graph8 mock/live API endpoints verification.
3. `test_llm_client`: Sentiment classification (Positive/Negative) verification.
4. `test_end_to_end_agent_loop`: Pure cyclical reinforcement loop (campaign creation → discovery → variant gen → 5 sends simulation → Bayesian evaluator → kill & evolution trigger).

---

## 6. Multi-Tenant Architecture & Mailbox Setup (Agency Clients)

- **Agency Multi-Tenant Support**:
  Har outgoing graph8 request mein `X-Target-Org-Id: <client_org_id>` header support add kar di gayi hai taake agency multiple client accounts ko ek single instance se manage kar sake.
- **Mailbox Connection in graph8**:
  graph8 native mailboxes use karta hai:
  1. graph8 Dashboard → **Settings** → **Mailboxes** → **New SMTP Mailbox**.
  2. Gmail ke liye apna **Google 16-Digit App Password** enter karein.
  3. Daily limit `50` aur warmup toggle enable karein.
  4. Save karne ke baad local dashboard ke **Mailbox Status** widget par status automatically **"Active ✅"** reflect ho jaye ga.
