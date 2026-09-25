# Santo Domingo Country Club — Voice Agent POC

A proof-of-concept multilingual (Spanish/English) voice assistant, **Sofia**,
for the [Santo Domingo Country Club](https://countryclub.do/). Built with
**LiveKit Agents** + **Google Gemini Live** (realtime speech-to-speech
model). All business data is mocked with static **JSON files** — no
database, ORM, or external API integration.

This matches the scope defined in `Santo Domingo Country Club Voice Agent
POC – Implementation Plan`.

## What it does

Sofia can answer voice questions about:

- **Club & activities** — general info, hours, contact, and sports/recreation
  (golf, tennis, padel, swimming, fitness, racquetball)
- **Golf** — course info, carts, caddies, golf shop, on-course dining,
  reservations
- **Restaurants** — the club's dining venues (Restaurante 1920, SportsBar,
  Hoyo 19, Mirador 18, Carro Bar, Piscina, Casa Tenis, Deli Gelato, Caseta 6,
  Caseta 12, Cigar Lounge)
- **Events** — event salons/venues, capacity, event types, facilities
- **Reservations** — explains the reservation process and links to the
  club's real booking platform (Golfmanager). **Does not complete real
  bookings** — explicitly out of scope for this POC.

## Architecture

```
country_club_agent/
├── app/
│   ├── main.py          # LiveKit worker entrypoint, wires Gemini Live
│   ├── agent.py          # CountryClubAgent (Sofia) + function tools
│   ├── prompts.py         # System instructions / persona
│   └── tools/
│       ├── __init__.py    # shared JSON loader (data/ access layer)
│       ├── activities.py  # get_activity_info / get_club_overview
│       ├── golf.py        # get_golf_info
│       ├── restaurants.py # get_restaurant_info
│       ├── events.py      # get_event_info
│       └── reservations.py# get_reservation_info
├── data/                   # MOCK data (source of truth for this POC)
│   ├── activities.json
│   ├── golf.json
│   ├── restaurants.json
│   └── events.json
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

```
Caller (voice)
     │
     ▼
LiveKit (room / audio transport)
     │
     ▼
AgentSession  ──uses──▶  Google Gemini Live (Realtime speech-to-speech,
     │                    native multilingual ES/EN, handles STT+LLM+TTS)
     │
     ▼
CountryClubAgent (Sofia)
     │
     ├── get_activity_info()      ─┐
     ├── get_club_overview()       │
     ├── get_golf_info()           ├─▶ app/tools/*.py ─▶ data/*.json (mock)
     ├── get_restaurant_info()     │
     ├── get_event_info()          │
     └── get_reservation_info()   ─┘
```

Design notes:

- **No DB/API layer.** `app/tools/__init__.py::load_json()` reads and caches
  the JSON files directly. Swapping this for a real backend later only
  means changing that one function — the tool signatures and agent code
  don't need to change.
- **Gemini Live handles multilingual speech end-to-end.** Rather than a
  separate STT → LLM → TTS pipeline, `google.beta.realtime.RealtimeModel`
  is used as a single realtime model, and language switching is handled by
  instructing the model (see `app/prompts.py`) to mirror the caller's
  language.
- **Tools return structured dicts, not prose.** The model composes the
  spoken reply itself from the tool's JSON result, per the persona rules in
  `prompts.py` (short, natural, no lists read verbatim).
- **Reservations are informational only.** `get_reservation_info()` always
  returns `reservation_confirmed: false` and only explains the process /
  shares the real booking link (`https://countryclub.golfmanager.com/...`).

## Setup

### 1. Requirements

- Python 3.11+
- A [LiveKit](https://livekit.io/) project (Cloud or self-hosted) — for
  `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- A Google AI Studio API key with access to Gemini Live — for
  `GOOGLE_API_KEY`

### 2. Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env with your real LiveKit + Google credentials
```

### 3. Run (local dev, with hot reload + local test room)

```bash
python -m app.main dev
```

This opens a LiveKit Agents dev session — connect with the LiveKit Agents
Playground (https://agents-playground.livekit.io/) pointed at your
`LIVEKIT_URL` to talk to Sofia by voice/text in the browser.

### 4. Run with Docker

```bash
docker compose up --build
```

## Example interactions

- "¿Qué actividades tiene el club?" → `get_activity_info()`
- "Tell me about golf" → `get_golf_info()`
- "¿Dónde puedo comer?" → `get_restaurant_info()`
- "How many people fit in Salón Cristal?" → `get_event_info("Salón Cristal")`
- "¿Puedo reservar golf?" → `get_reservation_info("golf")`

## Out of scope (see implementation plan §15)

Membership login/auth, OTP, real reservations/payments, membership
management, a real customer database, real-time booking availability, CRM
or WhatsApp integration, multi-agent orchestration, RAG/vector search,
production API integration. These are candidates for a future phase, at
which point `app/tools/__init__.py::load_json()` is the natural seam to
replace with real API/DB calls.

## Data source

Mock JSON content in `/data` was derived from the public site
[countryclub.do](https://countryclub.do/) (club overview, sports, dining
venue names) plus placeholder values from the implementation plan (e.g.
event salon capacities) that should be confirmed with the club before any
production use.
