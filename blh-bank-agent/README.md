# BLH Voice Agent — Proof of Concept

A voice-based banking assistant for **Banco López de Haro (BLH)**, built on
**LiveKit Agents** with **Google Gemini Live (Realtime API)** as the real-time,
multilingual speech-to-speech model.

**Voice/reasoning model:** Google Gemini Live (Realtime) API, via the
`livekit-plugins-google` `beta.realtime.RealtimeModel`. Gemini Live is
natively multilingual and multimodal, handling Spanish/English speech
in and out without a separate STT + LLM + TTS pipeline.

**No database, no ORM, no REST business API.** All mock data
(branches, products, loans, ATMs) lives in flat JSON files under
`mock_data/` and is loaded into memory at process start by
`agent/data_store.py`. Tool calls query that in-memory structure directly.

---

## 1. Architecture

```
blh-voice-agent-poc/
├── Dockerfile                      # Production container image
├── README.md                       # Setup and documentation
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── mock_data/                      # MOCK DATA (JSON)
│   ├── products.json               # Savings, accounts, cards, FX, deposits
│   ├── loans.json                  # Mortgage, vehicle, personal, fast loans
│   └── branches.json               # 15 branches, 10 ATMs, general contact
├── agent/                          # LiveKit voice agent package
│   ├── __init__.py
│   ├── config.py                   # Environment variable & model configuration
│   ├── data_store.py               # In-memory mock data store & query functions
│   ├── prompts.py                  # System instructions & persona
│   ├── main.py                     # Entrypoint: BLHAgent + Gemini RealtimeModel
│   ├── audio_trigger/              # Audio trigger for instant greeting
│   │   ├── __init__.py
│   │   ├── audio_trigger.py
│   │   └── hey.wav
│   └── tools/                      # Domain-specific function tools
│       ├── __init__.py             # Exports ALL_TOOLS list
│       ├── product_tools.py        # get_product_info
│       ├── loan_tools.py           # get_loan_info
│       ├── calculator_tools.py     # calculate_loan
│       ├── branch_tools.py         # find_branch, list_branches, find_atm
│       └── escalation_tools.py     # escalate_to_human
└── tests/
    └── test_calculator.py         # Unit tests for amortization math & tools
```

---

## 2. Setup

### Prerequisites
- Python 3.11+
- LiveKit Cloud project or self-hosted server ([cloud.livekit.io](https://cloud.livekit.io))
- Google Gemini API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))

### Installation

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in your credentials:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
GOOGLE_API_KEY=your_google_gemini_api_key
```

---

## 3. Running the Agent

### Development mode
```bash
python -m agent.main dev
```

### Production worker mode
```bash
python -m agent.main start
```

### Docker
```bash
docker build -t blh-voice-agent-poc .
docker run --env-file .env blh-voice-agent-poc
```

### Running Tests
```bash
python -m pytest tests/ -v
```

---

## 4. Key Tools

| Tool | Function | Description |
|---|---|---|
| `get_product_info` | [`product_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/product_tools.py) | Look up banking products & categories |
| `get_loan_info` | [`loan_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/loan_tools.py) | Look up loan requirements, documents & terms |
| `calculate_loan` | [`calculator_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/calculator_tools.py) | Estimate monthly loan payment using amortization math |
| `find_branch` | [`branch_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/branch_tools.py) | Search branch locations, hours & contact info |
| `list_branches` | [`branch_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/branch_tools.py) | List all bank branches |
| `find_atm` | [`branch_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/branch_tools.py) | Find ATM locations |
| `escalate_to_human` | [`escalation_tools.py`](file:///f:/blh-voice-agent-poc/agent/tools/escalation_tools.py) | Route complex or sensitive requests to a human |
