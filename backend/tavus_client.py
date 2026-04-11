"""
tavus_client.py - Create a Tavus CVI (Conversational Video Interface) session

Docs: https://docs.tavus.io/api-reference/conversations/create-conversation
"""

import os
import requests

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")    # Your avatar replica
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")    # Your character persona
TAVUS_BASE_URL = "https://tavusapi.com/v2"


def create_conversation(system_prompt: str, greeting: str, user_name: str = "there") -> dict:
    """
    Start a Tavus CVI session with injected health + calendar context.

    Returns:
        { conversation_url, conversation_id, status }
    """
    if not TAVUS_API_KEY:
        print("[tavus] No TAVUS_API_KEY set — returning mock conversation URL")
        return _mock_conversation()

    if not TAVUS_REPLICA_ID or not TAVUS_PERSONA_ID:
        print("[tavus] Missing REPLICA_ID or PERSONA_ID — returning mock")
        return _mock_conversation()

    headers = {
        "x-api-key": TAVUS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "replica_id": TAVUS_REPLICA_ID,
        "persona_id": TAVUS_PERSONA_ID,
        "conversation_name": f"Wellness Briefing",
        "conversational_context": system_prompt,
        "custom_greeting": greeting,
        "properties": {
            "max_call_duration": 600,           # 10 min max
            "participant_left_timeout": 30,
            "participant_absent_timeout": 60,
            "enable_recording": False,
            "apply_greenscreen": False,
        }
    }

    try:
        response = requests.post(
            f"{TAVUS_BASE_URL}/conversations",
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return {
            "conversation_url": data.get("conversation_url"),
            "conversation_id": data.get("conversation_id"),
            "status": data.get("status", "created")
        }
    except requests.RequestException as e:
        print(f"[tavus] API error: {e}")
        return _mock_conversation()


def end_conversation(conversation_id: str) -> bool:
    """End an active Tavus conversation."""
    if not TAVUS_API_KEY or not conversation_id:
        return False
    try:
        response = requests.delete(
            f"{TAVUS_BASE_URL}/conversations/{conversation_id}",
            headers={"x-api-key": TAVUS_API_KEY},
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
