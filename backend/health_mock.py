"""
health_mock.py - Wearable health data

Priority:
1. Transition API (Apple Watch / Apple Health) — set TRANSITION_API_KEY in .env
2. Mock data fallback
"""

import os
import requests
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def get_health_data() -> dict:
    """
    Returns today's health metrics.
    Uses Transition API (Apple Health) if key is set, otherwise mock.
    """
    transition_key = os.getenv("TRANSITION_API_KEY", "")
    if transition_key:
        try:
            data = get_transition_health_data(transition_key)
            print(f"[health] ✅ Real Apple Health data loaded via Transition API")
            return data
        except Exception as e:
            print(f"[health] ⚠️ Transition API failed ({e}), falling back to mock")
    else:
        print("[health] No TRANSITION_API_KEY set — using mock data")
    return get_mock_health_data()


def get_transition_health_data(api_key: str) -> dict:
    """
    Fetch real Apple Health data via Transition API.
    Docs: https://termo.ai/skills/apple-health-skill
    """
    base_url = "https://api.transition.fun/api/v1"
    headers = {"X-API-Key": api_key}

    # Ask the AI coach for today's health summary
    coach_res = requests.post(
        f"{base_url}/coach/chat",
        headers=headers,
        json={"message": (
            "Give me today's key health metrics as a JSON object with these exact fields: "
            "sleep_hours, sleep_score (0-100), hrv_ms, hrv_7day_avg, resting_hr, "
            "recovery_score (0-100), steps_yesterday. "
            "Use your best estimate from Apple Health data. Reply ONLY with the JSON object, no explanation."
        )},
        timeout=15
    )
    coach_res.raise_for_status()
    raw = coach_res.json()

    # Extract the message text and parse JSON
    import json, re
    text = raw.get("message", raw.get("response", str(raw)))
    match = re.search(r'\{[^}]+\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not parse JSON from Transition response: {text[:200]}")

    metrics = json.loads(match.group())

    # Also get PMC for fatigue/form scores
    try:
        pmc_res = requests.get(f"{base_url}/performance/pmc", headers=headers, timeout=10)
        pmc = pmc_res.json()
        tsb = pmc.get("tsb", 0)  # Training Stress Balance: negative = fatigued
        # Map TSB to a recovery score if not available
        if "recovery_score" not in metrics:
            metrics["recovery_score"] = max(0, min(100, int(50 + tsb)))
    except Exception:
        pass

    return {
        "date": str(date.today()),
        "sleep_hours": float(metrics.get("sleep_hours", 7.0)),
        "sleep_score": int(metrics.get("sleep_score", 75)),
        "hrv_ms": int(metrics.get("hrv_ms", 50)),
        "hrv_7day_avg": int(metrics.get("hrv_7day_avg", 55)),
        "resting_hr": int(metrics.get("resting_hr", 65)),
        "recovery_score": int(metrics.get("recovery_score", 70)),
        "steps_yesterday": int(metrics.get("steps_yesterday", 5000)),
        "calories_burned": int(metrics.get("calories_burned", 1800)),
        "stress_level": "moderate",
        "source": "apple_health_transition"
    }


def get_mock_health_data() -> dict:
    return {
        "date": str(date.today()),
        "sleep_hours": 6.2,
        "sleep_score": 71,        # out of 100
        "hrv_ms": 42,             # HRV in milliseconds
        "hrv_7day_avg": 56,       # 7-day average HRV
        "resting_hr": 68,         # bpm
        "recovery_score": 65,     # out of 100
        "steps_yesterday": 4200,
        "calories_burned": 1850,
        "stress_level": "moderate",  # low / moderate / high
        "source": "mock"
    }


# --- Real API Stubs ---

def get_oura_health_data(api_token: str) -> dict:
    """
    TODO: Connect to Oura Ring API
    Docs: https://cloud.ouraring.com/v2/docs
    """
    raise NotImplementedError("Plug in your Oura API token and implement this")


def get_fitbit_health_data(access_token: str) -> dict:
    """
    TODO: Connect to Fitbit Web API
    Docs: https://dev.fitbit.com/build/reference/web-api/
    """
    raise NotImplementedError("Plug in your Fitbit OAuth token and implement this")


def get_apple_health_data() -> dict:
    """
    TODO: Apple Health doesn't have a direct API.
    Options:
    - Export via Health Auto Export app → parse JSON
    - Use Apple HealthKit via a companion iOS app
    - Use Terra API (https://tryterra.co) as a unified wearable bridge
    """
    raise NotImplementedError("Use Health Auto Export or Terra API for Apple Health")
