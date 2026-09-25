# Amadita Laboratorio Clínico — Smart Voice Agent POC

A LiveKit-based voice agent for **Amadita Laboratorio Clínico** that can hold real, multi-step conversations with patients (check appointments, prep requirements, branch capabilities, book/reschedule, home service / servicio a domicilio, explain results, escalate to human staff) instead of just answering FAQs.

**Voice/reasoning model:** Google Gemini Live (Realtime) API, via the `livekit-plugins-google` `beta.realtime.RealtimeModel`. Gemini Live is natively multilingual/multimodal, handling Spanish and English speech seamlessly.

**No database, no ORM, no REST business API.** All backend data (branches, patients, tests, appointments, results) lives in flat JSON files under `mock_data/` and is loaded into memory at process start by `agent/data_store.py`. Tool calls read/mutate that in-memory structure directly (writes are flushed back to JSON files).

## Architecture

```
amadita/
├── agent/                         # The LiveKit Agent worker (Python)
│   ├── main.py                    # entrypoint: builds AgentSession + Gemini RealtimeModel
│   ├── config.py                  # env/config loading
│   ├── prompts.py                 # system instructions, Amadita branding, home service, escalation policies
│   ├── data_store.py              # loads mock_data/*.json into memory, read/write helpers
│   └── tools/                     # tool modules
│       ├── patient_tools.py       # lookup_patient, get_patient_history
│       ├── test_tools.py          # check_test_requirements
│       ├── branch_tools.py        # check_branch_capability, list_branches, find_branches_offering_test
│       ├── appointment_tools.py   # check_appointment_slots, book_appointment
│       ├── home_service_tools.py  # check_home_service, list_home_service_branches, book_home_service
│       ├── results_tools.py       # check_results_status, explain_result
│       ├── notify_tools.py        # send_confirmation
│       └── escalation_tools.py    # escalate_to_human
├── mock_data/                     # MOCK DATA (json) — branches, patients, tests, appointments, results
│   ├── branches.json              # Scraped real Amadita branches (Santo Domingo, Santiago, etc.)
│   ├── patients.json
│   ├── tests.json                 # Real Amadita catalogue: CBC, thyroid, lipid, glucose, imaging, etc.
│   ├── appointments.json
│   └── results.json
├── Dockerfile
├── requirements.txt
└── README.md
```

## Features & Use Cases

- **Branch Locator & Capabilities:** 74+ branches across the Dominican Republic (Gazcue 24h, Piantini, Naco, Bella Vista, Santiago, etc.) with operating hours, drive-thru / auto-servicio, and home service flags.
- **Catalogue & Prep Requirements:** Complete test catalog (Hemograma, Perfil lipídico, Glucosa, Perfil tiroideo, HbA1c, Vitamina D, Sonografía, Rayos X, Resonancia Magnética, Mamografía, Densitometría, etc.) with fasting and prep instructions.
- **Home Service (Servicio a Domicilio):** Check if requested tests can be sampled at home and book home visits.
- **Appointment Scheduling:** Check slot availability and book in-branch or home appointments.
- **Results Lookup & Explanation:** Check ready status and patient-friendly explanations.
- **Human Escalation:** Escalates complex medical questions, emergencies, or complaints to customer care.

## Setup

```bash
cd amadita
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Set environment variables: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, GOOGLE_API_KEY
python -m agent.main dev
```
