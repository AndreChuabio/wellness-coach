"""
health_mock.py - Wearable health data with 7-day trend history

Returns today's metrics + weekly history so Baymax can identify trends
and give advice like "your HRV has been declining all week."
"""

from datetime import date, timedelta


def get_health_data() -> dict:
    """
    Returns today's health metrics + 7-day history.
    """
    return get_mock_health_data()


def get_mock_health_data() -> dict:
    today = date.today()

    # 7-day history — realistic declining trend leading into today
    # Simulates a week of late nights, increasing stress, dropping HRV
    history = [
        {
            "date": str(today - timedelta(days=6)),
            "sleep_hours": 7.8, "sleep_score": 88,
            "hrv_ms": 61, "resting_hr": 62, "recovery_score": 85,
            "steps": 8200, "note": "Great start to the week"
        },
        {
            "date": str(today - timedelta(days=5)),
            "sleep_hours": 7.2, "sleep_score": 82,
            "hrv_ms": 58, "resting_hr": 63, "recovery_score": 80,
            "steps": 7400, "note": "Solid day"
        },
        {
            "date": str(today - timedelta(days=4)),
            "sleep_hours": 6.9, "sleep_score": 76,
            "hrv_ms": 54, "resting_hr": 65, "recovery_score": 74,
            "steps": 6100, "note": "Slight dip, busy day"
        },
        {
            "date": str(today - timedelta(days=3)),
            "sleep_hours": 6.5, "sleep_score": 72,
            "hrv_ms": 50, "resting_hr": 66, "recovery_score": 70,
            "steps": 5800, "note": "Late night, feeling it"
        },
        {
            "date": str(today - timedelta(days=2)),
            "sleep_hours": 6.1, "sleep_score": 68,
            "hrv_ms": 46, "resting_hr": 67, "recovery_score": 66,
            "steps": 4900, "note": "Tired, skipped workout"
        },
        {
            "date": str(today - timedelta(days=1)),
            "sleep_hours": 6.3, "sleep_score": 70,
            "hrv_ms": 44, "resting_hr": 68, "recovery_score": 64,
            "steps": 5100, "note": "Still dragging"
        },
    ]

    # Today's metrics — bottom of the dip
    today_data = {
        "date": str(today),
        "sleep_hours": 6.2,
        "sleep_score": 71,
        "hrv_ms": 42,
        "hrv_7day_avg": 56,       # avg of the week above
        "resting_hr": 68,
        "recovery_score": 65,
        "steps_yesterday": 5100,
        "calories_burned": 1850,
        "stress_level": "moderate",
        "source": "mock"
    }

    # Trend analysis — let Baymax reference these directly
    trend = _analyze_trend(history, today_data)

    return {
        **today_data,
        "history": history,
        "trend": trend
    }


def _analyze_trend(history: list, today: dict) -> dict:
    """Compute week-over-week trend signals for Baymax to reference."""
    hrv_values = [d["hrv_ms"] for d in history] + [today["hrv_ms"]]
    sleep_scores = [d["sleep_score"] for d in history] + [today["sleep_score"]]
    recovery_scores = [d["recovery_score"] for d in history] + [today["recovery_score"]]

    hrv_start = hrv_values[0]
    hrv_end = hrv_values[-1]
    hrv_direction = "declining" if hrv_end < hrv_start else "improving"
    hrv_delta = abs(hrv_end - hrv_start)

    sleep_avg = round(sum(sleep_scores) / len(sleep_scores), 1)
    recovery_avg = round(sum(recovery_scores) / len(recovery_scores), 1)

    consecutive_low_hrv = 0
    for d in reversed(history + [today]):
        if d["hrv_ms"] < 50:
            consecutive_low_hrv += 1
        else:
            break

    return {
        "hrv_trend": hrv_direction,
        "hrv_delta_7d": hrv_delta,
        "hrv_trend_summary": f"HRV has {hrv_direction} by {hrv_delta}ms over the past 7 days (from {hrv_start}ms to {hrv_end}ms)",
        "sleep_score_7day_avg": sleep_avg,
        "recovery_7day_avg": recovery_avg,
        "consecutive_days_low_hrv": consecutive_low_hrv,
        "weekly_insight": _generate_insight(hrv_direction, hrv_delta, sleep_avg, consecutive_low_hrv)
    }


def _generate_insight(hrv_trend: str, hrv_delta: int, sleep_avg: float, consecutive_low: int) -> str:
    """Generate a plain-English weekly insight for Baymax to reference."""
    if hrv_trend == "declining" and hrv_delta >= 15:
        return (
            f"This has been a tough week. HRV has dropped significantly over 7 days "
            f"and has been below 50ms for {consecutive_low} consecutive days. "
            f"The body is showing signs of accumulated stress. Prioritize sleep and light activity today."
        )
    elif hrv_trend == "declining" and hrv_delta >= 8:
        return (
            f"A gradual decline in recovery this week. HRV trending down, "
            f"sleep scores averaging {sleep_avg}/100. Worth being intentional about wind-down tonight."
        )
    elif hrv_trend == "improving":
        return (
            f"Good trajectory this week — HRV has been climbing. "
            f"Sleep averaging {sleep_avg}/100. Keep building on this momentum."
        )
    else:
        return f"Mixed week overall. Sleep averaging {sleep_avg}/100. Consistency is key."


# --- Real API Stubs (for future use) ---

def get_oura_health_data(api_token: str) -> dict:
    """TODO: Oura Ring API — https://cloud.ouraring.com/v2/docs"""
    raise NotImplementedError

def get_fitbit_health_data(access_token: str) -> dict:
    """TODO: Fitbit Web API — https://dev.fitbit.com"""
    raise NotImplementedError

def get_apple_health_data() -> dict:
    """TODO: Use Terra API (tryterra.co) or Health Auto Export app"""
    raise NotImplementedError
