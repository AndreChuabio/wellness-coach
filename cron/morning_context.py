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
load_dotenv(Path(__file__).parent.parent / ".env")

from health_mock import get_health_data
from calendar_fetch import get_calendar_events
from context_builder import build_system_prompt

OUTPUT_FILE = Path(__file__).parent.parent / "context.json"


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Building morning wellness context...")

    health = get_health_data()
    print(f"  Sleep: {health['sleep_hours']}h | HRV: {health['hrv_ms']}ms | Recovery: {health['recovery_score']}/100")

    events = get_calendar_events()
    print(f"  Calendar: {len(events)} events today")

    context = build_system_prompt(health, events)

    # Save to context.json
    output = {
        "generated_at": datetime.now().isoformat(),
        "health": health,
        "events": events,
        **context
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Context saved to {OUTPUT_FILE}")
    print(f"\n🌅 Today's Top Recommendations:")
    for i, rec in enumerate(context["recommendations"], 1):
        print(f"  {i}. [{rec['category'].upper()}] {rec['title']}")
        print(f"     {rec['detail'][:100]}...")

    print(f"\n💬 Greeting: {context['greeting']}")


if __name__ == "__main__":
    main()
