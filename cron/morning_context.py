"""
morning_context.py - Pre-build wellness context every morning at 6:30 AM

Run via cron:
  30 6 * * * /usr/bin/python3 /path/to/wellness-coach/cron/morning_context.py

Or via OpenClaw cron:
  openclaw cron add "30 6 * * *" "python3 ~/wellness-coach/cron/morning_context.py"
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv

# Load .env from project root — absolute path so it works from any cwd
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=True)
print(f"  Loading .env from: {_env_path} (exists: {_env_path.exists()})")

from health_mock import get_health_data
from calendar_fetch import get_calendar_events
from context_builder import build_system_prompt
from tavus_client import create_conversation
from users import USERS, display_name


def _output_file(user: str) -> Path:
    return Path(__file__).parent.parent / f"context_{user}.json"


def _build_for_user(user: str) -> None:
    print(f"\n=== {display_name(user)} ===")

    health = get_health_data(user)
    print(f"  Sleep: {health['sleep_hours']}h | HRV: {health['hrv_ms']}ms | Recovery: {health['recovery_score']}/100")

    events = get_calendar_events(user)
    print(f"  Calendar: {len(events)} events today")

    context = build_system_prompt(user, health, events)

    print("  Creating Tavus CVI session...")
    conversation = create_conversation(
        system_prompt=context["system_prompt"],
        greeting=context["greeting"],
        user_name=display_name(user),
    )
    conversation_url = conversation.get("conversation_url", "")
    is_mock = conversation.get("status") == "mock"
    print(f"  {'[MOCK] ' if is_mock else ''}Conversation URL: {conversation_url}")

    output_file = _output_file(user)
    output = {
        "generated_at": datetime.now().isoformat(),
        "user": user,
        "health": health,
        "events": events,
        "conversation_url": conversation_url,
        "conversation_id": conversation.get("conversation_id"),
        **context,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  ✅ Context saved to {output_file}")
    print(f"  💬 Greeting: {context['greeting']}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Building morning wellness context for all users...")

    tavus_key = os.getenv("TAVUS_API_KEY", "")
    tavus_replica = os.getenv("TAVUS_REPLICA_ID", "")
    tavus_persona = os.getenv("TAVUS_PERSONA_ID", "")
    print(f"  Tavus keys: API={'✅' if tavus_key else '❌ MISSING'} REPLICA={'✅' if tavus_replica else '❌ MISSING'} PERSONA={'✅' if tavus_persona else '❌ MISSING'}")

    for user in USERS:
        try:
            _build_for_user(user)
        except Exception as e:
            print(f"  ❌ Failed for {user}: {e}")


if __name__ == "__main__":
    main()
