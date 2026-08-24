# JMMB AI Voice Banking Assistant — POC

A working voice-first banking assistant built on **LiveKit Agents** using a
**Supervisor multi-agent pattern**, powered by **Google Gemini Realtime
(Live) API** for speech-to-speech conversation, with **mock JSON data**
standing in for real core-banking systems — no database, no ORM models, no
REST API layer.

## 1. Architecture

```
                        Customer (voice)
                              │
                              ▼
                     LiveKit Room / Track
                              │
                              ▼
                  ┌───────────────────────┐
                  │   Supervisor Agent     │
                  │  (Gemini Realtime)     │
                  │  • Greeting            │
                  │  • Onboarding          │
                  │  • OTP verification    │
                  │  • Intent detection    │
                  │  • Routing (handoff)   │
                  └───────────┬────────────┘
                              │  hands off control via
                              │  function_tool return value
        ┌───────────┬────────┴────────┬───────────────┐
        ▼           ▼                 ▼               ▼
  Financial      Loan             Service          Security
  Guidance       Assistance       Assistance       Assistance
  Agent          Agent            Agent            Agent
        │           │                 │               │
        └───────────┴────────┬────────┴───────────────┘
                              ▼
                     Mock Tool Layer (core/store.py)
                              ▼
                     mock JSON files (data/*.json)
```

This mirrors LiveKit's native **"Agents & Handoffs"** workflow pattern:

* Every specialist is a plain `Agent` subclass (its own instructions, its
  own `@function_tool` methods).
* **`session.userdata`** (see `core/userdata.py`) is a single shared
  dataclass carried across every agent in the session — this is how
  "once verified, the customer never repeats OTP" is implemented: the
  `verified` flag lives on shared session state, not inside any one agent.
* A **handoff** is just a tool call that returns a new `Agent` instance
  (optionally carrying over `chat_ctx` so the new agent remembers the
  conversation so far). The Supervisor is itself re-enterable, so
  cross-agent journeys (Scenario 5: Financial Guidance → Loan) work by
  specialists handing back to the Supervisor, or directly to a sibling
  specialist.
* There is **no database** — `core/store.py` is a tiny JSON
  read/append/query helper that treats each file in `data/` as a "table".
  Nothing here is production persistence; it's just enough to make demo
  tool calls return believable, stateful-looking data.

## 2. Project layout

```
jmmb-voice-poc/
├── agent.py                    # LiveKit worker entrypoint
├── config.py                   # env / model config
├── requirements.txt
├── .env.example
├── core/
│   ├── userdata.py             # shared session state (SessionUserData)
│   └── store.py                # JSON mock "DB" helper (no SQL/ORM)
├── prompts/
│   └── base.py                 # shared persona / house-style instructions
├── agents/
│   ├── supervisor.py           # SupervisorAgent — greeting/onboarding/OTP/routing
│   ├── financial_guidance.py   # FinancialGuidanceAgent
│   ├── loan.py                 # LoanAgent
│   ├── service.py              # ServiceAgent
│   └── Security.py                # SecurityAgent
└── data/                       # mock JSON "tables"
    ├── customers.json
    ├── accounts.json
    ├── loans.json
    ├── financial_products.json
    ├── service_branches.json
    ├── appointments.json
    └── Security_cases.json
```

## 3. Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then fill in .env:
#   LIVEKIT_URL=
#   LIVEKIT_API_KEY=
#   LIVEKIT_API_SECRET=
#   GOOGLE_API_KEY=              # Gemini API key (aistudio.google.com)
```

You need a LiveKit server/Cloud project (for the voice transport) and a
Google AI Studio API key (for the Gemini Realtime model). Both have free
tiers, which is all a POC needs.

## 4. Run

Console mode (talk to it straight from your terminal, no separate frontend
needed):

```bash
python agent.py console
```

Or run it as a normal LiveKit worker and connect any LiveKit-compatible
frontend (e.g. the [Agents Playground](https://agents-playground.livekit.io)):

```bash
python agent.py dev
```

## 5. Demo script (matches the POC's Section 8 scenarios)

1. **Greeting & onboarding** — say hello. The Supervisor asks for your
   name, phone, and email, "sends" a mock OTP (printed to the console
   logs — this stands in for the real SMS gateway) and asks you to read
   it back.
2. **Scenario 1 — Financial Guidance**: "I'm looking for a financial
   product that suits my needs" → routed to `FinancialGuidanceAgent`,
   which asks a couple of qualifying questions and recommends a product
   from `data/financial_products.json`.
3. **Scenario 2 — Loan**: "How much can I borrow and what would my
   monthly payment be?" → `LoanAgent` checks eligibility, calculates a
   payment with `calculate_loan_payment`, and offers to create a loan
   lead (`create_loan_lead`, written to `data/loans.json`).
4. **Scenario 3 — Service**: "I'd like to book a branch appointment" →
   `ServiceAgent` lists branches, checks a mock availability calendar,
   and books an appointment into `data/appointments.json`.
5. **Scenario 4 — Security**: "I see a transaction I don't recognize" →
   `SecurityAgent` looks up the mock account, opens a case in
   `data/Security_cases.json`, returns a case reference number, and flags
   serious cases for escalation.
6. **Scenario 5 — Cross-agent**: from Financial Guidance, ask "what would
   my monthly payment be if I financed this instead?" — the
   `FinancialGuidanceAgent` hands off directly to `LoanAgent` without
   re-verifying OTP, because `verified` lives in shared `userdata`.

## 6. What this POC intentionally does NOT do

Per the spec's Section 9 — no real core-banking integration, no real
transfers/approvals, no real OTP/SMS, no real Security engine, no production
security/compliance, no database. All tool calls read/write local JSON
files in `data/`.
