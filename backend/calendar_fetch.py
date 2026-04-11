"""
calendar_fetch.py - Fetch today's calendar events via gog CLI

Runs `gog calendar list --days 1` and parses output.
Falls back to mock data if gog is unavailable.
"""

import subprocess
import json
import re
from datetime import datetime


def get_calendar_events() -> list[dict]:
    """
    Returns today's calendar events as a list of dicts.
    Falls back to mock data if gog CLI is not available.
    """
    try:
        result = subprocess.run(
            ["gog", "calendar", "list", "--days", "1"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return parse_gog_output(result.stdout)
        else:
            print(f"[calendar] gog returned non-zero or empty: {result.stderr}")
            return get_mock_calendar()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[calendar] gog not available ({e}), using mock data")
        return get_mock_calendar()


def parse_gog_output(raw: str) -> list[dict]:
    """
    Parse gog calendar output into structured events.
    Adjust regex if gog output format differs.
    """
    events = []
    lines = raw.strip().split("\n")
    for line in lines:
        # Try to match lines like: "9:00 AM - Team Standup (30 min)"
        match = re.match(r"(\d{1,2}:\d{2}\s?[AP]M)\s*[-–]\s*(.+?)(?:\s*\((\d+)\s*min\))?$", line, re.IGNORECASE)
        if match:
            time_str, title, duration = match.groups()
            events.append({
                "time": time_str.strip(),
                "title": title.strip(),
                "duration_min": int(duration) if duration else 60
            })
        elif line.strip() and not line.startswith("#"):
            # Fallback: include raw line as event title
            events.append({
                "time": "TBD",
                "title": line.strip(),
                "duration_min": 60
            })
    return events if events else get_mock_calendar()


def get_mock_calendar() -> list[dict]:
    return [
        {"time": "9:00 AM",  "title": "Team Standup",          "duration_min": 30,  "type": "meeting"},
        {"time": "11:00 AM", "title": "Deep Work Block",        "duration_min": 180, "type": "focus"},
        {"time": "2:00 PM",  "title": "Client Presentation",   "duration_min": 60,  "type": "high_stakes"},
        {"time": "4:00 PM",  "title": "1:1 with Manager",      "duration_min": 30,  "type": "meeting"},
    ]


def summarize_calendar(events: list[dict]) -> dict:
    """Return a quick summary dict for the context builder."""
    meeting_count = sum(1 for e in events if e.get("type") in ("meeting", "high_stakes", None))
    has_high_stakes = any(e.get("type") == "high_stakes" for e in events)
    focus_blocks = [e for e in events if e.get("type") == "focus"]
    return {
        "total_events": len(events),
        "meeting_count": meeting_count,
        "has_high_stakes_meeting": has_high_stakes,
        "focus_block_available": len(focus_blocks) > 0,
        "events": events,
    }
