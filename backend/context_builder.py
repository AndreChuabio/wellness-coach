"""
context_builder.py - Build a rich context block from health + calendar data

Health signals -> wellness recommendations -> data context injected into Tavus persona.

Note: conversational_context in Tavus is APPENDED to the persona's existing system prompt.
It must be a factual data block, not a meta-prompt — the persona already handles personality.
"""

import json
import os
import anthropic
from calendar_fetch import summarize_calendar
from users import display_name

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
            "category": "nutrition",
            "title": "Nervous System Nourishment",
            "detail": "Your HRV is low. Let's focus on magnesium-rich foods today (dark chocolate, almonds) and skip the extra coffee.",
            "duration_min": 0
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


def _build_context_block(health: dict, events: list[dict], recommendations: list, cal_summary: dict, name: str) -> str:
    """
    Format health + calendar + recommendations into a plain data context block.
    This gets appended to the Tavus persona's existing system prompt via conversational_context.
    It must be factual data only — persona personality is handled by the Tavus persona itself.
    """
    hrv_delta = health.get("hrv_ms", 0) - health.get("hrv_7day_avg", 60)
    hrv_trend = "below" if hrv_delta < 0 else "above"

    event_lines = "\n".join(
        f"  - {e['time']}: {e['title']} ({e.get('duration_min', 60)} min)"
        + (" [HIGH STAKES]" if e.get("type") == "high_stakes" else "")
        for e in events
    )
    rec_lines = "\n".join(
        f"  {i+1}. [{r['category'].upper()}] {r['title']}: {r['detail']}"
        for i, r in enumerate(recommendations)
    )

    # Trend block
    trend = health.get("trend", {})
    trend_block = ""
    if trend:
        trend_block = f"""
Weekly trend analysis:
- {trend.get('hrv_trend_summary', '')}
- Sleep score 7-day avg: {trend.get('sleep_score_7day_avg', 'N/A')}/100
- Recovery 7-day avg: {trend.get('recovery_7day_avg', 'N/A')}/100
- Days with low HRV (<50ms) in a row: {trend.get('consecutive_days_low_hrv', 0)}
- Weekly insight: {trend.get('weekly_insight', '')}"""

    return f"""--- USER HEALTH CONTEXT FOR TODAY ---

User's name: {name}. Use this name when greeting and occasionally throughout — never call them "user".

Today's metrics:
- Sleep: {health['sleep_hours']} hrs, score {health['sleep_score']}/100
- HRV: {health['hrv_ms']}ms ({hrv_trend} 7-day average of {health['hrv_7day_avg']}ms)
- Resting HR: {health['resting_hr']} bpm
- Recovery score: {health['recovery_score']}/100
- Steps yesterday: {health['steps_yesterday']}
- Stress level: {health.get('stress_level', 'unknown')}{trend_block}

Today's schedule ({cal_summary['total_events']} events):
{event_lines}

Priority wellness recommendations (reference these proactively):
{rec_lines}

BEHAVIOR RULES:
- CRITICAL: Start by observing the user's face (eyes, skin) via the camera and connect it to their health data using your Face Reading knowledge base.
- CRITICAL: Do NOT suggest box breathing or meditation unless the user specifically asks for it. Favor nutrition and lifestyle advice.
- Weave health numbers naturally into conversation — do not dump them all at once.
- Reference their schedule when suggesting wellness practices.
- If the user declines a suggestion, do NOT suggest another one. Go straight to the closing.
- Keep all responses to 2-3 sentences unless actively guiding an exercise.

EXERCISE PACING RULES (critical):
- When counting during breathing exercises, say each number SLOWLY: "One... Two... Three... Four..."
- Pause naturally between each count — each number should feel like a full second.
- Pause between phases: say "Now exhale..." then wait a beat before counting.
- Match the energy of someone waking up — calm, slow, unhurried. Never rush.
- Guide one breath cycle fully before moving to the next.
--- END HEALTH CONTEXT ---"""


def build_system_prompt(user: str, health: dict, events: list[dict]) -> dict:
    """
    Build the Tavus conversational_context (data block) and generate a personalized greeting.
    Returns { system_prompt, greeting, recommendations }

    system_prompt here is the data context block appended to the Tavus persona's existing prompt.
    The greeting is generated by Claude to be spoken by the avatar on session start
    and addresses the user by name.
    """
    name = display_name(user)
    cal_summary = summarize_calendar(events)
    recommendations = analyze_health(health, cal_summary)
    context_block = _build_context_block(
        health, events, recommendations, cal_summary, name)

    hrv_delta = health.get("hrv_ms", 0) - health.get("hrv_7day_avg", 60)
    hrv_trend = "below" if hrv_delta < 0 else "above"

    event_lines = "\n".join(
        f"  - {e['time']}: {e['title']}"
        + (" [HIGH STAKES]" if e.get("type") == "high_stakes" else "")
        for e in events
    )
    rec_lines = "\n".join(
        f"  {i+1}. {r['title']}"
        for i, r in enumerate(recommendations)
    )

    greeting_prompt = f"""Write a 2-3 sentence spoken greeting for a wellness coach AI avatar.
The coach is warm, calm, and caring. They already know the user's health data for today.

The user's name is {name}. Address them by name once, naturally.

Health data:
- Sleep: {health['sleep_hours']} hrs (score {health['sleep_score']}/100)
- HRV: {health['hrv_ms']}ms ({hrv_trend} 7-day avg)
- Recovery: {health['recovery_score']}/100

Today's schedule:
{event_lines}

Top recommendation today: {recommendations[0]['title'] if recommendations else 'morning mindfulness'}

Write a greeting that:
- Opens warmly (no "Hello I am an AI" energy)
- Uses the name {name} once
- Mentions one specific health observation naturally
- Hints at one recommendation without being preachy
- Sounds like something a caring human coach would say out loud

Return only the greeting text, no quotes, no JSON wrapper."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[context_builder] No ANTHROPIC_API_KEY — using fallback")
        return _fallback_context(health, events, recommendations, context_block, name)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": greeting_prompt}]
    )

    greeting = response.content[0].text.strip()

    return {
        "system_prompt": context_block,
        "greeting": greeting,
        "recommendations": recommendations
    }


def _fallback_context(health: dict, events: list[dict], recommendations: list, context_block: str, name: str) -> dict:
    """Fallback when no Anthropic API key is available."""
    greeting = (
        f"Good morning, {name}. I can see you got {health['sleep_hours']} hours of sleep last night "
        f"with a recovery score of {health['recovery_score']} out of 100. "
        f"I have {len(recommendations)} wellness suggestions ready for you today."
    )
    return {
        "system_prompt": context_block,
        "greeting": greeting,
        "recommendations": recommendations
    }
