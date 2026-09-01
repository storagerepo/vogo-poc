# Referencia Laboratorio — Smart Voice Agent POC

A LiveKit-based voice agent that proves an AI can hold a real, multi-step
conversation with a patient (check appointments, prep rules, branch
capabilities, book/reschedule, explain results, escalate) instead of just
answering FAQs — per the POC plan.

**Voice/reasoning model:** Google Gemini Live (Realtime) API, via the
`livekit-plugins-google` `beta.realtime.RealtimeModel`. Gemini Live is
natively multilingual/multimodal, so it handles Spanish/English speech
in and out without a separate STT→LLM→TTS pipeline.

**No database, no ORM, no REST business API.** All "backend" data
(branches, patients, tests, appointments, results) lives in flat JSON
files under `agent/data/` and is loaded into memory at process start by
`agent/data_store.py`. Tool calls read/mutate that in-memory structure
directly (writes are also flushed back to the JSON files so state
survives a reload during the demo). This is intentionally disposable —
in production this whole module is swapped for real LIS/scheduling
API clients, per §11 of the POC plan.

The only "server" in this repo besides the LiveKit agent worker is a
10-line **token endpoint** (`token_server/`), which is unavoidable
LiveKit plumbing (a browser/phone can't join a LiveKit room without a
signed access token) — it is not a data/business API.

## Architecture

```
referencia-voice-poc/
├── agent/                     # The LiveKit Agent worker (Python)
│   ├── main.py                 # entrypoint: builds AgentSession + Gemini RealtimeModel
│   ├── config.py                # env/config loading
│   ├── prompts.py                # system instructions, language-lock + escalation policy text
│   ├── language.py               # language-detection + "lock after first turn" state machine
│   ├── data_store.py              # loads /data/*.json into memory, read/write helpers, persists back to disk
│   ├── data/                      # MOCK DATA ONLY (json) — branches, patients, tests, appointments, results
│   │   ├── branches.json
│   │   ├── patients.json
│   │   ├── tests.json
│   │   ├── appointments.json
│   │   └── results.json
│   └── tools/                     # one module per tool family from POC §3
│       ├── patient_tools.py        # lookup_patient, get_patient_history
│       ├── test_tools.py            # check_test_requirements
│       ├── branch_tools.py           # check_branch_capability
│       ├── appointment_tools.py       # check_appointment_slots, book_appointment
│       ├── results_tools.py            # check_results_status, explain_result
│       ├── notify_tools.py              # send_confirmation
│       └── escalation_tools.py           # escalate_to_human
├── web/                        # Static demo site mimicking labreferencia.com
│   ├── index.html               # hero + branch list (from real site copy) + "Habla con el asistente" widget
│   ├── style.css
│   └── app.js                    # LiveKit JS SDK: gets token, joins room, mic in/out, renders transcript+tool trace
├── token_server/               # Minimal LiveKit access-token issuer (FastAPI, ~1 route)
│   └── main.py
├── scripts/
│   ├── run_agent.sh
│   └── run_token_server.sh
├── docs/
│   └── ARCHITECTURE.md
├── requirements.txt
└── .env.example
```

### Why this shape

- **`agent/tools/*`** — each file mirrors one row of the POC §3 tool
  table 1:1, and each function has a docstring the model reads as its
  function-calling schema. Splitting by domain (patient / test / branch
  / appointment / results / notify / escalation) keeps each file small
  and matches how a human front-desk system is organized (patient file
  system, test reference sheet, booking calendar, LIS, ticketing).
- **`agent/data_store.py`** is the *only* place that touches the JSON
  files. Tools never open files directly — they call
  `data_store.get_patient(...)`, `data_store.book(...)`, etc. That's the
  seam where real LIS/scheduling clients get swapped in later (§11),
  with zero changes needed in `tools/` or `main.py`.
- **`agent/language.py`** implements POC §2: agent opens in English,
  listens to the *first* user turn, detects Spanish vs English with a
  lightweight detector, and then locks the session's instructions to
  that language for every subsequent turn (confirmations, results,
  escalation — all of it). It does not re-detect per turn.
- **`web/`** is a static mock of labreferencia.com's homepage (same
  hero copy/branch cards style as the real site) with a floating
  "Habla con el asistente" voice widget, so stakeholders can literally
  click and talk to the agent in a browser — this is the "Web
  chat/voice widget" channel from POC §5. `app.js` also renders the
  live tool-call trace (POC §3 "each tool call is visible in a
  debug/transcript panel", and §9 success criteria).
- **Phone channel (§5)**: not wired to a real SIP trunk in this zip
  (needs a real LiveKit Cloud project + SIP trunk + phone number,
  which are account-specific secrets), but `docs/ARCHITECTURE.md`
  documents exactly how to attach LiveKit SIP so the same
  `agent/main.py` answers real inbound calls with no code changes —
  that's the whole point of building it on LiveKit Agents.

## Setup

```bash
cd referencia-voice-poc
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in .env: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GOOGLE_API_KEY
```

Run the agent worker:

```bash
bash scripts/run_agent.sh        # python -m agent.main dev
```


```bash
bash scripts/run_token_server.sh # uvicorn token_server.main:app --port 8080
```

## Mock data

Branch names/addresses are pulled from the real labreferencia.com
sucursales list (Piantini, Naco/HS Medical Center, Bella Vista/Red
Médica, Santiago Ágora, La Vega) but capabilities, hours-this-week,
patients, appointments and results are 100% fictional — see
`agent/data/*.json`. No real patient data is used anywhere, per POC §6.
