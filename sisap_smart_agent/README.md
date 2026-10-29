# SISAP Smart Agent POC (LiveKit + Gemini Live)

A multilingual voice agent for enterprise cybersecurity and IT support, built with LiveKit Agents and Google Gemini Live (realtime speech-to-speech). Follows the unified Vogo POC architectural pattern.

- **Technical Support**: VPN / firewall / network help -> knowledge retrieval -> simulated diagnostics -> ticket creation -> engineer handoff
- **SOC Analyst Copilot**: alert triage -> auth & endpoint log search -> event correlation -> investigation report -> analyst handoff

Voice runs natively on the **Gemini Live realtime model** (speech-in / speech-out). It automatically detects the speaker's language and replies in it (English, Spanish, Portuguese, Hindi, etc.). All tool definitions and internal arguments stay in English to guarantee reliable retrieval over the mock datasets.

---

## Project Structure (Vogo Pattern)

```
sisap_smart_agent/
├── agent/
│   ├── __init__.py
│   ├── main.py                  # LiveKit worker entrypoint: AgentSession, audio trigger, metrics
│   ├── instructions.py          # System instructions: persona, workflows, guardrails, rules
│   ├── audio_trigger/           # Direct-to-buffer WAV greeting trigger
│   │   ├── __init__.py
│   │   ├── audio_trigger.py
│   │   └── greeting.wav
│   └── tools/                   # LiveKit @function_tool wrappers + domain logic
│       ├── __init__.py          # Exports ALL_TOOLS list
│       ├── data_store.py        # Mock backend, domain errors, session state, access rules
│       ├── routing.py           # route_request_tool
│       ├── knowledge.py         # search_knowledge_tool (scoped RAG)
│       ├── support.py           # Support workflow tools (diagnostics, tickets, escalation)
│       └── soc.py               # SOC workflow tools (alerts, logs, correlation, reports)
├── mock_data/                   # Mock JSON fixtures (alerts, auth_logs, endpoint_events, tickets, etc.)
├── knowledge/                   # Markdown guides & incident playbooks
├── eval/                        # Evaluation & testing suite
│   ├── test_conversations.md    # Scripted eval conversations & scoring rubric
│   └── test_agent_tools.py      # Automated unit & integration tests
├── Dockerfile                   # Container packaging with agent.main entrypoint
├── docker-compose.yml           # Local deployment with mock_data volume persistence
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Clean project dependencies
└── .env.example                 # Environment variables template
```

---

## Quick Start

### 1. Setup Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Set your keys in `.env`:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `GOOGLE_API_KEY`

### 2. Run the Agent

**Console Mode (talk directly from your mic & headphones):**
```bash
python -m agent.main console
```

**Dev Mode (join room via LiveKit Agents Playground):**
```bash
python -m agent.main dev
```

**Production Start (used inside Docker):**
```bash
python -m agent.main start
```

### 3. Run Automated Evals & Tests
```bash
pytest -v
```

---

## Key Design Principles

1. **Deterministic Workflow Routing**: The LLM classifies intent in English and calls `route_request_tool`. The agent sets the active workflow (`technical_support` or `soc_copilot`) and scopes tool permissions.
2. **Strict Guardrails & Human Confirmation**: State-changing actions (`create_ticket`, `escalate_to_human`, `hand_off_to_analyst`) require explicit confirmation. Destructive containment actions (blocking IPs, disabling accounts, modifying firewall rules) are strictly forbidden and refused.
3. **Grounded Correlation**: The SOC Copilot generates investigation reports strictly from retrieved log records and correlation timelines. Unsupported speculations or hallucinated events are barred.
4. **Resilient Persistence**: Tickets, reports, and audit trails persist atomically in `mock_data/` JSON fixtures.
