"""
token_server.py

Minimal token server for the POC test client. Issues short-lived LiveKit
room access tokens so a browser (LiveKit Agents Playground, or any
LiveKit JS/React client) can join a room that the agent worker (agent/main.py)
will also join.

This is intentionally tiny — no auth, no UI (per the plan, visual/UI
design is out of scope for this POC). For anything beyond local demo use,
put real auth in front of /token.

Run:
    uvicorn token_server:app --reload --port 8080

Then request a token:
    GET http://localhost:8080/token?room=vogo-demo&identity=tester
"""

from __future__ import annotations

import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit import api

load_dotenv()

app = FastAPI(title="Vogo Voice Concierge POC — Token Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # POC only — restrict this in anything beyond local demo use
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/token")
def get_token(
    room: str = Query(default="vogo-demo", description="Room name to join"),
    identity: str | None = Query(default=None, description="Caller identity"),
) -> dict:
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret or not livekit_url:
        raise HTTPException(
            status_code=500,
            detail="Missing LIVEKIT_API_KEY / LIVEKIT_API_SECRET / LIVEKIT_URL in environment",
        )

    identity = identity or f"tester-{uuid.uuid4().hex[:6]}"

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )

    return {
        "token": token.to_jwt(),
        "url": livekit_url,
        "room": room,
        "identity": identity,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
