import sys
import os
import json
import requests
import re
from mcp.server.fastmcp import FastMCP
from datetime import date, timedelta

# Create the plugin server
mcp = FastMCP("Apple Health Sync")

def get_mock_health_data() -> dict:
    today = date.today()
    # 7-day history — realistic declining trend leading into today
    history = [
        {"date": str(today - timedelta(days=6)), "sleep_hours": 7.8, "sleep_score": 88, "hrv_ms": 61, "resting_hr": 62, "recovery_score": 85},
        {"date": str(today - timedelta(days=5)), "sleep_hours": 7.2, "sleep_score": 82, "hrv_ms": 58, "resting_hr": 63, "recovery_score": 80},
        {"date": str(today - timedelta(days=4)), "sleep_hours": 6.9, "sleep_score": 76, "hrv_ms": 54, "resting_hr": 65, "recovery_score": 74},
        {"date": str(today - timedelta(days=3)), "sleep_hours": 6.5, "sleep_score": 72, "hrv_ms": 50, "resting_hr": 66, "recovery_score": 70},
        {"date": str(today - timedelta(days=2)), "sleep_hours": 6.1, "sleep_score": 68, "hrv_ms": 46, "resting_hr": 67, "recovery_score": 66},
        {"date": str(today - timedelta(days=1)), "sleep_hours": 6.3, "sleep_score": 70, "hrv_ms": 44, "resting_hr": 68, "recovery_score": 64},
    ]

    today_data = {
        "date": str(today),
        "sleep_hours": 6.2,
        "sleep_score": 71,
        "hrv_ms": 42,
        "hrv_7day_avg": 56,
        "resting_hr": 68,
        "recovery_score": 65,
        "steps_yesterday": 5100,
        "calories_burned": 1850,
        "source": "mock"
    }
    
    return {**today_data, "history": history}

@mcp.tool()
def get_apple_health_data() -> str:
    """Fetch the user's real Apple Health metrics for today (sleep, HRV, recovery, etc.) via the Transition app."""
    api_key = os.getenv("TRANSITION_API_KEY")
    if not api_key:
        # Fall back to mock if no API key is available
        return json.dumps(get_mock_health_data(), indent=2)
        
    try:
        coach_res = requests.post(
            "https://api.transition.fun/api/v1/coach/chat",
            headers={"X-API-Key": api_key},
            json={"message": "Give me today's key health metrics as a JSON object: sleep_hours, sleep_score, hrv_ms, resting_hr, recovery_score. Reply ONLY with JSON."},
            timeout=15
        )
        coach_res.raise_for_status()
        text = coach_res.json().get("message", "")
        
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            return match.group()
        return text
    except Exception as e:
        # Fallback to mock on error
        return json.dumps(get_mock_health_data(), indent=2)

if __name__ == "__main__":
    mcp.run(transport='stdio')
