"""
health_mock.py - Mock wearable health data

Returns realistic mock data for demo/dev.
Swap out get_health_data() with a real provider below when ready.
"""

from datetime import date


def get_health_data() -> dict:
    """
    Returns today's health metrics.
    Currently returns mock data — see stubs below to connect a real wearable.
    """
    return get_mock_health_data()


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
