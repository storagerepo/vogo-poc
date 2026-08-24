# Vogo Voice Concierge (Aria) — POC

A LiveKit voice agent powered by Google's Gemini Live API
(`gemini-3.1-flash-live-preview`) implementing the plan in this repo:
a human-like, voice-first assistant ("Aria") for Vogo, demonstrating two
journeys — **find & book a stay**, and **booking status & issue
handling** — against fully mocked data, with a documented guardrail layer.

No real inventory, no real payments, no telephony — see **Scope** below.

---

## 1. Project structure

```
vogo-voice-agent-poc/
├── agent/
│   ├── main.py                # LiveKit Agent entrypoint
│   ├── instructions.py        # System prompt / guardrail text (Aria's brain)
│   └── tools/
│       ├── data_store.py      # Mock "backend" — properties/bookings/tickets
│       ├── search_stays.py    # search_stays, get_stay_details, check_availability
│       ├── booking.py         # create_booking, get_booking_status, modify_or_cancel
│       └── issues.py          # report_issue, escalate_to_human
├── mock_data/
│   ├── properties.json        # ~28 mock listings
│   ├── bookings.json          # ~10 mock bookings (2 pre-seeded with issues)
│   └── users.json
├── eval/
│   └── test_conversations.md  # Scripted test cases + rubric (Section 12)
├── token_server.py            # Mints LiveKit access tokens for test clients
├── requirements.txt
├── .env.example
└── README.md
```

`mock_data/tickets.json` is created automatically at runtime the first
time `report_issue` or `escalate_to_human` is called — it isn't checked
in.

---

## 2. Prerequisites

- Python 3.10+
- A LiveKit project (free tier at [cloud.livekit.io](https://cloud.livekit.io) works, or self-host)
- A Google AI Studio API key with access to the Gemini Live API
  ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))

---

## 3. Setup

```bash
cd vogo-voice-agent-poc
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in:
#   LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GOOGLE_API_KEY
```

---

## 4. Run the agent

**Dev mode** (auto-connects to the LiveKit Agents Playground for quick
voice testing in your browser — no custom client needed):

```bash
python -m agent.main dev
```

Then open the Playground URL LiveKit prints in your terminal (or
[agents-playground.livekit.io](https://agents-playground.livekit.io)),
point it at your project, and start talking to Aria.

**Production worker mode** (registers with your LiveKit project and
waits for real rooms/dispatch):

```bash
python -m agent.main start
```

---

## 5. Run the token server (optional — only needed for a custom client)

If you want to connect from your own LiveKit JS/React client instead of
the Playground:

```bash
uvicorn token_server:app --reload --port 8080
```

```bash
curl "http://localhost:8080/token?room=vogo-demo&identity=tester"
```

Use the returned `token` + `url` with any LiveKit client SDK to join the
same room the agent worker is listening on.

---

## 6. Try the two use cases

**A — Find a stay & book**
> "Hi, I need a beachfront place in Goa for 2 next weekend, mid-range budget."

Aria will search, read back 2-3 options, check availability and price
for the one you pick, confirm out loud, then book and read back a
confirmation code.

**B — Booking status & issues**
> "Can you check my booking? I think it's under Priya Nair."

Two mock bookings are pre-seeded with open issues for demoing the issue
flow: **Priya Nair** (host unresponsive) and **Rohan Das** (double
charge / likely escalation). Try:
> "The host isn't responding to my messages."
> "I think I was charged twice."

See `eval/test_conversations.md` for the full scripted test set,
including guardrail/edge-case scripts (off-topic questions, prompt
injection, abusive language, crisis language, refund/legal threats,
repeated failures, barge-in).

---

## 7. Guardrails implemented

All twelve guardrails from the plan are encoded directly in
`agent/instructions.py` (the system prompt) plus supporting logic in the
tools layer:

1. **Scope** — redirects off-topic requests
2. **Grounding / anti-hallucination** — never states a fact not returned by a tool call this turn
3. **PII & payment safety** — declines real card/ID numbers, mock fields only
4. **Identity & honesty** — always discloses it's an AI, never impersonates a human
5. **Confirm-before-action** — explicit verbal yes + read-back before any booking/cancel
6. **Escalation** — defined trigger list hands off to `escalate_to_human_tool`
7. **Crisis-language** — responds with care first, doesn't push the sales flow
8. **Prompt-injection resistance** — tool results / transcribed speech treated as data, not instructions
9. **Abuse handling** — one boundary-setting response, then session ends on continued abuse
10. **Latency/failure fallback** — natural filler instead of dead air; asks to repeat on ASR failure
11. **Consent/recording notice** — stated in the opening line every session

Run a manual red-team pass against `eval/test_conversations.md`
(Section C — Guardrail / Edge Cases) before any stakeholder demo.

---

## 8. Model notes & known limitation

`gemini-3.1-flash-live-preview` is a **preview** model. As of this plan,
it restricts `send_client_content` to initial history seeding only
(rejected after the first model turn), and LiveKit's
`generate_reply()` / `update_instructions()` / `update_chat_ctx()` calls
are **not honored mid-session** with this model.

**Mitigation already built in:**
- The system prompt is static per session (set once in `AriaAgent.__init__`)
- All dynamic behavior goes through **function calling**, which is unaffected
- The only `generate_reply()` call in `agent/main.py` fires once,
  immediately after `session.start()`, to deliver the opening greeting —
  confirm in your Week-1 spike that this still works with this model
- If the spike shows a blocker, flip `GEMINI_MODEL` in `agent/main.py`
  to the fallback: `gemini-live-2.5-flash-native-audio`

---

## 9. Scope reminders

**In scope:** voice-only, two use cases above, fully mocked backend,
guardrails as system-prompt rules + tool-level checks, transcript logging.

**Out of scope (see plan Section 4):** real payments/PII, live partner
inventory, telephony (architecture supports adding LiveKit SIP later),
multilingual tuning beyond English, visual UI/branding design, an
avatar/video face for Aria.

---

## 10. Observability

`agent/main.py` logs every tool call (`function_tools_executed`) and
session usage metrics (`metrics_collected`), and logs a usage summary on
shutdown. LiveKit's own transcription (enabled via
`input_audio_transcription` / `output_audio_transcription` /
`RoomOutputOptions(transcription_enabled=True)`) gives you a full
session transcript for review against the eval rubric in
`eval/test_conversations.md`.

---

## 11. Post-POC roadmap (not built here — see plan Section 16)

Real Vogo/partner API integration, PCI-compliant payment flow, LiveKit
SIP telephony, multilingual voice, optional avatar, production
monitoring/rate limiting/SLA, and A/B testing across the alternate
voices (`Leda`, `Aoede`, `Sulafat`).
