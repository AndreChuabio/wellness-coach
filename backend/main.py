"""
main.py - FastAPI backend for Wellness Coach AI (multi-user: Andre + Nikki)

Endpoints (all require X-App-Password header except / and /static/*):
  GET  /health-data?user=...        → today's wearable metrics
  POST /health-sync?user=...        → ingest Apple Watch metrics from iOS Shortcut
  GET  /health-sync/status?user=... → last sync status
  GET  /calendar?user=...           → today's calendar events
  POST /start-session               → build context + create Tavus CVI session
  GET  /context?user=...            → pre-built context (for cron use case)
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from health_mock import get_health_data, ingest_shortcut_payload, _load_cache
from calendar_fetch import get_calendar_events
from context_builder import build_system_prompt
from tavus_client import create_conversation
from users import USERS, is_valid, display_name
from startup import materialize_railway_creds

# Run Railway base64 → file materialization once at import time so all
# downstream calendar reads find their per-user token files.
materialize_railway_creds()

logger = logging.getLogger(__name__)

app = FastAPI(title="Wellness Coach AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def context_file(user: str) -> Path:
    return Path(__file__).parent.parent / f"context_{user}.json"


FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def resolve_user(user: str = Query(..., description="andre or nikki")) -> str:
    if not is_valid(user):
        raise HTTPException(status_code=400, detail=f"unknown user '{user}'")
    return user


def verify_password(x_app_password: str | None = Header(default=None)) -> None:
    expected = os.getenv("APP_PASSWORD")
    if not expected:
        # No password configured server-side — allow through. Useful for
        # local dev where you don't want the prompt.
        return
    if x_app_password != expected:
        raise HTTPException(status_code=401, detail="bad password")


class StartSessionRequest(BaseModel):
    user: str


class HealthSyncPayload(BaseModel):
    user: str
    hrv_ms: float | None = None
    resting_hr: float | None = None
    sleep_hours: float | None = None
    steps_yesterday: float | None = None
    calories_burned: float | None = None


@app.get("/")
def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "ok", "app": "Wellness Coach AI"}


@app.get("/debug-env")
def debug_env():
    """Quick check that all env vars are loaded (values masked). Public on purpose."""
    def mask(val):
        if not val: return "❌ MISSING"
        return f"✅ {val[:6]}..."
    return {
        "APP_PASSWORD":        mask(os.getenv("APP_PASSWORD")),
        "ANTHROPIC_API_KEY":   mask(os.getenv("ANTHROPIC_API_KEY")),
        "TAVUS_API_KEY":       mask(os.getenv("TAVUS_API_KEY")),
        "TAVUS_REPLICA_ID":    mask(os.getenv("TAVUS_REPLICA_ID")),
        "TAVUS_PERSONA_ID":    mask(os.getenv("TAVUS_PERSONA_ID")),
        "TRANSITION_API_KEY":  mask(os.getenv("TRANSITION_API_KEY")),
        "GOOGLE_TOKEN_ANDRE":  mask(os.getenv("GOOGLE_TOKEN_PICKLE_B64_ANDRE")),
        "GOOGLE_TOKEN_NIKKI":  mask(os.getenv("GOOGLE_TOKEN_PICKLE_B64_NIKKI")),
    }


@app.post("/health-sync", dependencies=[Depends(verify_password)])
def health_sync(payload: HealthSyncPayload):
    """
    Ingest Apple Watch metrics posted by the iOS Shortcut.
    Derives sleep_score and recovery_score, appends to rolling 7-day cache.
    """
    if not is_valid(payload.user):
        raise HTTPException(status_code=400, detail=f"unknown user '{payload.user}'")
    try:
        data = payload.model_dump()
        data.pop("user", None)
        record = ingest_shortcut_payload(data, payload.user)
        logger.info("Health sync (%s): hrv=%s resting_hr=%s sleep=%sh",
                    payload.user, record.get("hrv_ms"), record.get("resting_hr"), record.get("sleep_hours"))
        return {"status": "ok", "synced_at": datetime.now(timezone.utc).isoformat(), "record": record}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health sync failed for %s: %s", payload.user, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health-sync/status", dependencies=[Depends(verify_password)])
def health_sync_status(user: str = Depends(resolve_user)):
    """Report when data was last received from the Shortcut for this user."""
    cache = _load_cache(user)
    if not cache:
        return {"status": "no_data", "user": user,
                "message": f"No Apple Watch data received yet for {user} — run the iOS Shortcut."}
    return {
        "status":       "ok" if cache.get("source") == "apple_watch" else "mock",
        "user":         user,
        "source":       cache.get("source"),
        "last_sync":    cache.get("date"),
        "hrv_ms":       cache.get("hrv_ms"),
        "sleep_hours":  cache.get("sleep_hours"),
    }


@app.get("/health-data", dependencies=[Depends(verify_password)])
def health_data(user: str = Depends(resolve_user)):
    """Return today's wearable health metrics for this user."""
    return get_health_data(user)


@app.get("/calendar", dependencies=[Depends(verify_password)])
def calendar(user: str = Depends(resolve_user)):
    """Return today's calendar events for this user."""
    return {"events": get_calendar_events(user)}


@app.post("/start-session", dependencies=[Depends(verify_password)])
def start_session(req: StartSessionRequest):
    """
    Full pipeline:
    1. Fetch health + calendar data for `user`
    2. Build Claude-generated system prompt + greeting (addressed to user)
    3. Create Tavus CVI session
    4. Return conversation URL + recommendations
    """
    if not is_valid(req.user):
        raise HTTPException(status_code=400, detail=f"unknown user '{req.user}'")
    try:
        health = get_health_data(req.user)
        events = get_calendar_events(req.user)
        context = build_system_prompt(req.user, health, events)

        conversation = create_conversation(
            system_prompt=context["system_prompt"],
            greeting=context["greeting"],
            user_name=display_name(req.user)
        )

        return {
            "conversation_url": conversation["conversation_url"],
            "conversation_id": conversation["conversation_id"],
            "status": conversation["status"],
            "greeting": context["greeting"],
            "recommendations": context["recommendations"],
            "health_summary": {
                "sleep_score": health["sleep_score"],
                "hrv_ms": health["hrv_ms"],
                "recovery_score": health["recovery_score"],
            },
            "event_count": len(events)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context", dependencies=[Depends(verify_password)])
def get_context(user: str = Depends(resolve_user)):
    """Return the pre-built context from the morning cron job for this user (if available)."""
    path = context_file(user)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    # Fall back to building live
    health = get_health_data(user)
    events = get_calendar_events(user)
    return build_system_prompt(user, health, events)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
