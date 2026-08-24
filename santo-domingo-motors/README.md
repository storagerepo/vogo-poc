# Santo Domingo Motors — AI Voice Agent (POC)

A voice-first customer experience for Sales, Service, and Finance, built on
**LiveKit Agents** using a **Supervisor multi-agent pattern**. No database —
all data is mock JSON "tables" under `/data`, so the POC runs standalone and
the storage layer (`app/data_store.py`) is the single seam to swap in real
systems later.

## Architecture — Supervisor Pattern

```
                         Customer (voice, via website)
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     SupervisorAgent    │  <- entry point for every call
                         │  (understands intent,  │
                         │   never calls domain   │
                         │   tools itself)        │
                         └───────────┬────────────┘
                    transfer_to_*    │    human_handoff
              ┌───────────┬──────────┴─────────┬───────────┐
              ▼           ▼                    ▼           ▼
        ┌───────────┐┌───────────┐      ┌────────────┐  ┌────────┐
        │ SalesAgent││ServiceAgent│      │FinanceAgent│  │ Human  │
        └─────┬─────┘└─────┬─────┘      └──────┬─────┘  │ Team   │
              │            │                   │         └────────┘
              ▼            ▼                   ▼
        sales_tools.py service_tools.py  finance_tools.py
              │            │                   │
              └────────────┼───────────────────┘
                            ▼
                     app/data_store.py
                            │
                            ▼
                  /data/*.json  (mock "tables")
```

- **SupervisorAgent** (`app/agents/supervisor.py`) is the single entry point.
  It greets the caller, classifies intent, and hands off the LiveKit
  `AgentSession` to the right specialist agent by returning a new `Agent`
  instance from a `function_tool` — this is LiveKit's native multi-agent
  handoff mechanism, and is what makes this a *Supervisor pattern*: one
  routing brain, several specialist workers.
- **SalesAgent / ServiceAgent / FinanceAgent** (`app/agents/*.py`) each own
  their department's tools only, matching the POC scope in the plan
  (sections 4–6). Each can hand back to the Supervisor
  (`return_to_supervisor`) or escalate to a human (`human_handoff`), both
  defined once on the shared `DepartmentAgent` base class
  (`app/agents/base.py`) so every department gets consistent handoff
  behavior for free.
- **Tools** (`app/tools/*.py`) are plain, framework-free Python functions —
  they don't import LiveKit at all. This keeps business logic unit-testable
  (`tests/`) and makes it trivial to later swap `app/data_store.py` for real
  APIs without touching agent code.
- **Mock data** (`/data/*.json`) stands in for `vehicles`, `sales_leads`,
  `test_drive_bookings`, `service_appointments`, `finance_leads`,
  `finance_rules`, plus slot-availability tables — matching section 10 of
  the POC plan. `app/data_store.py` is the only file that touches the
  filesystem.

## Project layout

```
santo-domingo-voice-agent/
├── app/
│   ├── main.py                # LiveKit worker entrypoint (Supervisor pattern wiring)
│   ├── config.py               # env-driven settings (LiveKit + Gemini Realtime)
│   ├── data_store.py           # JSON-file "mock DB" layer
│   ├── agents/
│   │   ├── base.py             # DepartmentAgent: shared human_handoff / return_to_supervisor
│   │   ├── supervisor.py       # SupervisorAgent: intent routing / handoff
│   │   ├── sales_agent.py      # Sales tools as function_tools
│   │   ├── service_agent.py    # Service tools as function_tools
│   │   └── finance_agent.py    # Finance tools as function_tools
│   ├── tools/                  # framework-free business logic (unit-testable)
│   │   ├── sales_tools.py
│   │   ├── service_tools.py
│   │   ├── finance_tools.py
│   │   └── common_tools.py     # human_handoff mock implementation
│   ├── models/schemas.py       # dataclass shape references for the mock tables
│   └── utils/                  # logger, ID generators
├── data/                       # mock JSON "tables" (no DB required)
├── tests/                      # pytest unit tests for the tool layer
├── requirements.txt
└── .env.example
```

## Voice model — Google Gemini Realtime

This POC uses **Gemini's realtime (speech-to-speech) model** as a single
combined STT + LLM + TTS engine, via LiveKit's `google.beta.realtime`
plugin (`app/main.py`):

```python
llm=google.beta.realtime.RealtimeModel(
    model=settings.GEMINI_REALTIME_MODEL,   # e.g. "gemini-2.0-flash-live-001"
    voice=settings.GEMINI_VOICE,            # e.g. "Puck"
    temperature=settings.GEMINI_TEMPERATURE,
    api_key=settings.GOOGLE_API_KEY,
)
```

There's no separate STT/TTS pipeline to wire up — audio in, understanding,
and audio out are handled by the one model. The **same** `AgentSession` /
model instance is reused across the whole call; only the *active* `Agent`
(instructions + tools) changes on each Supervisor handoff, so voice, latency
characteristics, and conversation memory stay consistent as the customer
moves between Sales, Service, and Finance.

> Gemini's live/realtime model ids change fairly often. Before running the
> POC, check [LiveKit's Google plugin docs](https://docs.livekit.io/agents/integrations/google/)
> and [Google AI Studio](https://aistudio.google.com/) for the current model
> id and update `GEMINI_REALTIME_MODEL` in `.env` if needed.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in LiveKit + Google (Gemini) keys
```

You need:
- A LiveKit server (LiveKit Cloud or self-hosted OSS) → `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- A Google API key with access to the Gemini Live/Realtime API → `GOOGLE_API_KEY` (from [Google AI Studio](https://aistudio.google.com/apikey))

## Run

```bash
python -m app.main dev     # local dev, connects to your LiveKit server
```

Then connect a frontend to the same room (e.g. LiveKit's
[Agents Playground](https://agents-playground.livekit.io/), or embed the
LiveKit web/mobile SDK in the Santo Domingo Motors website) to talk to the
agent by voice.

## Sandbox note

This sandbox has no network access to livekit.io / Google's API, so
`pip install -r requirements.txt` and the actual `python -m app.main dev`
call were **not** run here. Every Python file was syntax-checked
(`py_compile`) and the framework-free tool layer was verified with the
included `pytest` suite (10/10 passing) — install the requirements and add
real LiveKit + Google credentials to run the live voice agent.

## Run tests

The tool layer has no LiveKit dependency, so tests run instantly without any
API keys or network access:

```bash
pip install pytest python-dotenv
pytest -q
```

## Swapping mock data for real systems

Every "table" read/write goes through `app/data_store.py`
(`read_table`, `write_table`, `append_record`, `find_one`, `find_all`).
To connect real systems (CRM, DMS, financing engine):

1. Keep the same function signatures in `data_store.py`.
2. Replace the JSON file I/O inside each function with real API/DB calls.
3. Nothing in `app/tools/*.py` or `app/agents/*.py` needs to change.

## Scope (matches the POC plan)

| Area | Capabilities |
|---|---|
| 🚗 Sales | Find Vehicle, Compare Models, Price Info, Test Drive Booking, Create Sales Lead |
| 🔧 Service | Service Inquiry, Check Availability, Book Appointment, Confirm Appointment, Service Details |
| 💰 Finance | Financing Info, Basic Eligibility, Payment Estimate, Create Finance Lead |
| 👨‍💼 Common | Human Handoff (available from Supervisor and every department) |

Insurance, parts, and other automotive services are out of scope, per the
POC plan.
