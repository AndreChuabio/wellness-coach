"""
tavus_client.py - Create a Tavus CVI (Conversational Video Interface) session

Docs: https://docs.tavus.io/api-reference/conversations/create-conversation
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TAVUS_BASE_URL = "https://tavusapi.com/v2"
MAX_SESSION_MINUTES = 5  # Keep it snappy — this is a morning briefing, not therapy

# Read at call time (not module load) so .env changes are picked up


def _get_keys():
    return (
        os.getenv("TAVUS_API_KEY"),
        os.getenv("TAVUS_REPLICA_ID"),
        os.getenv("TAVUS_PERSONA_ID"),
    )


SESSION_RULES = """
--- SESSION RULES ---
Objectives (follow in order):
1. Greet warmly and deliver the health summary (sleep, HRV, recovery) in 2-3 sentences.
2. Present the top 2 wellness recommendations clearly and concisely.
3. Ask if the user wants to be guided through a quick wellness exercise. If yes, guide them step by step. If no, skip to closing.
4. Close with one motivational sentence tailored to their day ahead, then end the session.

Guardrails:
- Keep the entire session under 5 minutes. If it has gone on for 4+ minutes, wrap up immediately.
- Keep all responses to 2-3 sentences max unless actively guiding an exercise.
- Never give medical diagnoses, prescribe medication, or present health data as medical advice.
- Never discuss topics unrelated to wellness, health, or the user's day ahead.
- If the user expresses a mental health crisis or emergency, gently refer them to a professional and end the session.
--- END SESSION RULES ---"""


def create_conversation(system_prompt: str, greeting: str, user_name: str = "there") -> dict:
    """
    Start a Tavus CVI session with injected health + calendar context.

    Returns:
        { conversation_url, conversation_id, status }
    """
    api_key, replica_id, persona_id = _get_keys()

    if not api_key:
        print("[tavus] No TAVUS_API_KEY set — returning mock conversation URL")
        return _mock_conversation()

    if not replica_id or not persona_id:
        print(
            f"[tavus] Missing REPLICA_ID={replica_id!r} or PERSONA_ID={persona_id!r} — returning mock")
        return _mock_conversation()

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Tavus CVI payload — conversational_context injects our Claude-built system prompt
    # custom_greeting is spoken by the avatar immediately on join
    payload = {
        "replica_id": replica_id,
        "persona_id": persona_id,
        "conversation_name": "Wellness Briefing",
        "conversational_context": system_prompt + "\n\n" + SESSION_RULES,
        "custom_greeting": greeting,
        "properties": {
            "max_call_duration": MAX_SESSION_MINUTES * 60,  # hard cutoff
            "participant_left_timeout": 20,
            "participant_absent_timeout": 30,
            "enable_recording": False,
            "apply_greenscreen": False,
            "language": "english",
            "enable_closed_captions": True,
        }
    }

    print(
        f"[tavus] Creating conversation with replica={replica_id} persona={persona_id}")
    print(f"[tavus] Greeting: {greeting[:80]}...")

    try:
        response = requests.post(
            f"{TAVUS_BASE_URL}/conversations",
            headers=headers,
            json=payload,
            timeout=15
        )
        print(
            f"[tavus] Response {response.status_code}: {response.text[:300]}")
        response.raise_for_status()
        data = response.json()
        return {
            "conversation_url": data.get("conversation_url"),
            "conversation_id": data.get("conversation_id"),
            "status": data.get("status", "created")
        }
    except requests.RequestException as e:
        print(f"[tavus] API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[tavus] Response body: {e.response.text}")
        return _mock_conversation()


def end_conversation(conversation_id: str) -> bool:
    """End an active Tavus conversation."""
    api_key, _, _ = _get_keys()
    if not api_key or not conversation_id:
        return False
    try:
        response = requests.delete(
            f"{TAVUS_BASE_URL}/conversations/{conversation_id}",
            headers={"x-api-key": api_key},
            timeout=10
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def _mock_conversation() -> dict:
    """
    Mock conversation for development without Tavus keys.
    Returns a Daily.co test room or placeholder.
    """
    return {
        "conversation_url": "https://tavus.daily.co/mock-wellness-session",
        "conversation_id": "mock-id-12345",
        "status": "mock",
        "note": "Set TAVUS_API_KEY, TAVUS_REPLICA_ID, TAVUS_PERSONA_ID in .env to use real Tavus CVI"
    }
