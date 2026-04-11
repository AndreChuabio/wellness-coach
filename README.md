# Wellness Coach AI

A conversational AI wellness coach that knows your health data and calendar — powered by Tavus CVI, Claude, and Google Calendar.

## Demo Flow

1. App opens → Healthmaxx greets you, already knowing your sleep score, HRV, and today's meetings
2. You speak naturally: "How am I doing today?"
3. Healthmaxx responds in real-time video: "Your HRV is a bit low. Want me to guide you through a box breathing session?"
4. Live guided breathing / meditation / wellness coaching — interactive, personalized

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│  index.html + app.js                         │
│  - Health stats sidebar                      │
│  - Calendar sidebar                          │
│  - Tavus CVI iframe (live video)             │
│  - Wellness recommendations                  │
└──────────────┬──────────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────────┐
│                  Backend (FastAPI)            │
│  main.py                                     │
│  ├── health_mock.py  (wearable data)         │
│  ├── calendar_fetch.py  (Google Calendar API)│
│  ├── context_builder.py  (Claude API)        │
│  └── tavus_client.py  (Tavus CVI API)        │
└──────────────┬──────────────────────────────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼           ▼
Anthropic    Tavus       Google
(Claude)     (CVI)      Calendar
```

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/AndreChuabio/wellness-coach
cd wellness-coach

pip install -r backend/requirements.txt

cp .env.example .env
# Edit .env with your API keys (see section below)
```

### 2. Set API Keys

Edit `.env`:

```
ANTHROPIC_API_KEY=...
TAVUS_API_KEY=...
TAVUS_REPLICA_ID=...
TAVUS_PERSONA_ID=...
```

Google Calendar is optional — the app falls back to mock schedule data if not configured.

### 3. Google Calendar Setup (optional but recommended)

This is a one-time OAuth flow that connects the app to your personal Google Calendar.

**Prerequisites:**
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Select or create a project
- Enable the Google Calendar API
- Go to APIs and Services → Credentials → Create OAuth 2.0 Client ID (Desktop app)
- Download the JSON and save it as `credentials.json` in the `wellness-coach/` folder
- Go to OAuth consent screen → Test users → add your Gmail address

**Run the setup script** (from the `wellness-coach/` root, not `backend/`):

```bash
python3 setup_gcal.py
```

A browser window will open. Sign in with your Google account and approve access. A `token.pickle` file will be saved locally.

**Add the paths to `.env`:**

```
GOOGLE_CREDENTIALS_PATH=/absolute/path/to/wellness-coach/credentials.json
GOOGLE_TOKEN_PATH=/absolute/path/to/wellness-coach/token.pickle
```

The setup script prints the exact paths to copy after it completes.

Note: `credentials.json` and `token.pickle` are gitignored and should never be committed.

### 4. Run the Backend

```bash
cd backend
python3 -m uvicorn main:app --reload
# Running at http://localhost:8000
```

### 5. Open the Frontend

```bash
open frontend/index.html
```

Or serve it locally:

```bash
cd frontend && python3 -m http.server 3000
# http://localhost:3000
```

Click "Start Morning Briefing" — the avatar will greet you by name with context from your real calendar and health data.

---

## Connecting Real Wearable Data

Health data is currently mocked in `backend/health_mock.py`. Replace `get_health_data()` with a real wearable integration:

### Oura Ring
```python
from health_mock import get_oura_health_data
data = get_oura_health_data(api_token="your_oura_token")
```
Token: https://cloud.ouraring.com/personal-access-tokens

### Fitbit
```python
from health_mock import get_fitbit_health_data
data = get_fitbit_health_data(access_token="your_fitbit_token")
```
Token: https://dev.fitbit.com

### Apple Health
Use [Health Auto Export](https://www.healthexportapp.com/) to export JSON, then parse in `health_mock.py`.
Or use [Terra API](https://tryterra.co) as a unified wearable bridge.

---

## Cron Job (Morning Context Pre-build)

Pre-build the AI context at 6:30 AM so sessions start instantly:

```bash
# Test it manually
python3 cron/morning_context.py

# Add to crontab
crontab -e
30 6 * * * /usr/bin/python3 /path/to/wellness-coach/cron/morning_context.py
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Avatar + Video | [Tavus CVI](https://tavus.io) |
| LLM Brain | [Claude](https://anthropic.com) (Haiku) |
| Calendar | Google Calendar API (OAuth) |
| Backend | FastAPI + Python |
| Frontend | Vanilla JS, no build step |
| Scheduler | cron |
