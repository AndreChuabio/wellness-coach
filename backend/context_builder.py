"""
context_builder.py - Build a rich Claude system prompt from health + calendar data

Health signals → wellness recommendations → Baymax persona system prompt
"""

import os
import anthropic
from calendar_fetch import summarize_calendar

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def analyze_health(health: dict, cal_summary: dict) -> list[dict]:
    """
    Map health signals to wellness recommendations.
    Returns a list of recommendation dicts.
    """
    recs = []
    hrv = health.get("hrv_ms", 0)
    hrv_avg = health.get("hrv_7day_avg", 60)
    sleep_score = health.get("sleep_score", 80)
    recovery = health.get("recovery_score", 75)
    has_high_stakes = cal_summary.get("has_high_stakes_meeting", False)
    meeting_count = cal_summary.get("meeting_count", 0)

    # HRV-based
    if hrv < 50:
        recs.append({
            "priority": "high",
            "category": "breathing",
            "title": "Box Breathing Session",
            "detail": "Your HRV is below your 7-day average — your nervous system needs support. "
                      "Try 4 rounds of box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s.",
            "duration_min": 5
        })
        recs.append({
            "priority": "medium",
            "category": "recovery",
            "title": "Recovery Day",
            "detail": "Skip intense exercise today. Light walk or gentle stretching only.",
            "duration_min": 20
        })

    # Sleep-based
    if sleep_score < 75:
        recs.append({
            "priority": "high",
            "category": "sleep",
            "title": "Strategic Nap Window",
            "detail": "Your sleep score was low. A 20-min nap between 1-3 PM can restore alertness "
                      "without affecting tonight's sleep. Avoid caffeine after 2 PM.",
            "duration_min": 20
        })

    # High-stakes meeting prep
    if has_high_stakes:
        recs.append({
            "priority": "high",
            "category": "breathing",
            "title": "Pre-Meeting Calm Protocol",
            "detail": "Before your big meeting, do 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s. "
                      "Repeat 4 cycles. This activates your parasympathetic nervous system.",
            "duration_min": 3
        })

    # Packed schedule
    if meeting_count >= 4:
        recs.append({
            "priority": "medium",
            "category": "meditation",
            "title": "Micro-Meditations Between Meetings",
            "detail": "Heavy meeting day — set a 2-min timer between each meeting. Close your eyes, "
                      "focus on your breath. Prevents cognitive fatigue from stacking.",
            "duration_min": 2
        })

    # Good recovery — push harder
    if recovery >= 80 and hrv >= hrv_avg:
        recs.append({
            "priority": "medium",
            "category": "movement",
            "title": "Great Recovery — Push Today",
            "detail": "Your body is primed. Consider a morning workout or cold shower to boost "
                      "dopamine and set a strong tone for the day.",
            "duration_min": 30
        })

    # Default if no recs
    if not recs:
        recs.append({
            "priority": "low",
            "category": "mindfulness",
            "title": "Morning Mindfulness",
            "detail": "Start with 5 minutes of quiet breathing or journaling to set your intention.",
            "duration_min": 5
        })

    return recs[:3]  # Top 3 recommendations


def build_system_prompt(health: dict, events: list[dict]) -> dict:
    """
    Generate a Baymax wellness coach system prompt using Claude.
    Returns { system_prompt, greeting, recommendations }
    """
    cal_summary = summarize_calendar(events)
    recommendations = analyze_health(health, cal_summary)

    hrv_delta = health.get("hrv_ms", 0) - health.get("hrv_7day_avg", 60)
    hrv_trend = "below" if hrv_delta < 0 else "above"

    event_lines = "\n".join(
        f"  - {e['time']}: {e['title']} ({e.get('duration_min', 60)} min)"
        for e in events
    )
    rec_lines = "\n".join(
        f"  {i+1}. [{r['category'].upper()}] {r['title']}: {r['detail']}"
        for i, r in enumerate(recommendations)
    )

    prompt = f"""You are generating a system prompt for an AI wellness coach named Baymax.

Baymax is warm, caring, precise, and health-obsessed (like the Disney character).
He speaks in a calm, supportive tone. He uses "I am not fast, I am thorough" energy.
He gently encourages but never lectures. He celebrates small wins.

Here is the user's health data for today:
- Sleep: {health['sleep_hours']} hours, score {health['sleep_score']}/100
- HRV: {health['hrv_ms']}ms ({hrv_trend} 7-day avg of {health['hrv_7day_avg']}ms)
- Resting HR: {health['resting_hr']} bpm
- Recovery score: {health['recovery_score']}/100
- Steps yesterday: {health['steps_yesterday']}

Today's calendar ({cal_summary['total_events']} events):
{event_lines}

Top wellness recommendations for today:
{rec_lines}

Generate:
1. A system prompt (3-5 paragraphs) for the Baymax wellness coach persona that:
   - Instructs the AI to stay in Baymax character
   - Embeds the health context naturally
   - Tells the AI what wellness recommendations to proactively offer
   - Instructs the AI to guide breathing/meditation exercises interactively when asked
   - Keeps responses warm, concise, and actionable

2. A personalized greeting (2-3 sentences) Baymax would say when the user opens the app.

Respond in JSON format:
{{
  "system_prompt": "...",
  "greeting": "..."
}}"""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[context_builder] No ANTHROPIC_API_KEY — using fallback prompt")
        return _fallback_context(health, events, recommendations)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    text = response.content[0].text
    # Extract JSON from response
    start = text.find("{")
    end = text.rfind("}") + 1
    parsed = json.loads(text[start:end])

    return {
        "system_prompt": parsed["system_prompt"],
        "greeting": parsed["greeting"],
        "recommendations": recommendations
    }


def _fallback_context(health: dict, events: list[dict], recommendations: list) -> dict:
    """Fallback when no API key is available."""
    greeting = (
        f"Hello! I am Baymax, your personal wellness companion. "
        f"I see you got {health['sleep_hours']} hours of sleep last night "
        f"with a recovery score of {health['recovery_score']}/100. "
        f"I have {len(recommendations)} wellness suggestions for you today. "
        f"Shall we get started?"
    )
    system_prompt = (
        "You are Baymax, a warm and caring AI wellness coach. "
        "You have access to the user's health data and calendar for today. "
        "Offer wellness advice including breathing exercises, meditation, and movement. "
        "When asked to guide an exercise, walk through it step by step. "
        "Keep responses concise, warm, and actionable."
    )
    return {
        "system_prompt": system_prompt,
        "greeting": greeting,
        "recommendations": recommendations
    }
