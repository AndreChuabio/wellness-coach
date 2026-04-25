"""
setup_gcal.py - One-time Google Calendar OAuth setup (per user)

Run this ONCE per user to authorize the app and save a token_<user>.pickle file.
After that, calendar_fetch.py will use it automatically.

Usage:
  1. Go to console.cloud.google.com
  2. Create a project → Enable Google Calendar API
  3. APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
  4. Download the JSON → save as credentials.json in this folder
  5. Run: python3 setup_gcal.py --user andre
     (or --user nikki — the user must sign in with their own Google account)
  6. Add to .env (local dev) or Railway env (deploy):
       Local:    GOOGLE_CREDENTIALS_PATH=../credentials.json
       Railway:  GOOGLE_CREDENTIALS_JSON=<paste raw credentials.json>
                 GOOGLE_TOKEN_PICKLE_B64_<USER>=<the base64 printed below>
"""

import argparse
import base64
import os
import pickle
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Ensure we can import users.py for the allowlist
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from users import USERS  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDS_FILE = "credentials.json"


def main():
    parser = argparse.ArgumentParser(description="Per-user Google Calendar OAuth setup")
    parser.add_argument("--user", required=True, choices=list(USERS),
                        help="Which user is signing in")
    args = parser.parse_args()

    token_file = f"token_{args.user}.pickle"
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                print(f"❌ {CREDS_FILE} not found!")
                print("Download it from: console.cloud.google.com → APIs & Services → Credentials")
                return
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    print(f"✅ Token saved to {token_file}")
    print()
    print("For local dev, add to your .env:")
    print(f"  GOOGLE_CREDENTIALS_PATH={os.path.abspath(CREDS_FILE)}")
    print()
    print("For Railway, paste this as an env var:")
    with open(token_file, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    print(f"  GOOGLE_TOKEN_PICKLE_B64_{args.user.upper()}={b64}")


if __name__ == "__main__":
    main()
