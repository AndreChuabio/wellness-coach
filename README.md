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

For Railway deployment, you can also inject the credentials directly via environment variables instead of uploading files:

```
GOOGLE_CREDENTIALS_JSON="<raw credentials.json content>"
GOOGLE_TOKEN_PICKLE_B64="<base64 of token.pickle>"
```

The backend will materialize these into local files at startup so Google Calendar can work in the deployed app.

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

## Deploying on Railway

This repo is Railway-ready using the root-level `Procfile`.

1. Create a Railway account at https://railway.app.
2. Create a new project and connect this GitHub repo, or use the Railway CLI:

```bash
cd /path/to/wellness-coach
railway init
```

3. Make sure Railway uses your project root and the following start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

4. Set the required environment variables in Railway:

- `ANTHROPIC_API_KEY`
- `TAVUS_API_KEY`
- `TAVUS_REPLICA_ID`
- `TAVUS_PERSONA_ID`

Optional variables:

- `ELEVENLABS_API_KEY`
- `GOOGLE_CREDENTIALS_PATH`
- `GOOGLE_TOKEN_PATH`

5. Deploy the service.

Railway will install `backend/requirements.txt` and start the FastAPI app from `backend/main.py`.

> If you want a free/hackathon-friendly setup, Railway is the cheapest and easiest choice for this FastAPI backend.

---

## Connecting Real Apple Watch Data

Health data defaults to a realistic 7-day mock in `backend/health_mock.py`. To pull live Apple Watch data, use the iOS Shortcut approach — no third-party app or paid tier required.

### How it works

An iOS Shortcut reads your Apple Watch metrics from HealthKit and POSTs them to `POST /health-sync`. The backend stores a rolling 7-day cache in `health_cache.json` (gitignored). `get_health_data()` returns cached data if it was synced today, otherwise falls back to mock.

Sleep score and recovery score are derived on the backend from raw metrics — no upstream service computes them.

### iOS Shortcut setup (one-time, ~10 min)

Build a Shortcut on your iPhone with these actions in order:

1. **Find Health Samples** → Heart Rate Variability → last 24h → Calculate Average → save as `hrv`
2. **Find Health Samples** → Resting Heart Rate → last 24h → Get latest → save as `resting_hr`
3. **Find Health Samples** → Sleep Analysis → last 24h → sum Asleep hours → save as `sleep_hours`
4. **Find Health Samples** → Step Count → yesterday → sum → save as `steps`
5. **Find Health Samples** → Active Energy Burned → today → sum → save as `calories`
6. **Get Contents of URL** → your backend URL + `/health-sync` → Method: POST → JSON body:

```json
{
  "hrv_ms": hrv,
  "resting_hr": resting_hr,
  "sleep_hours": sleep_hours,
  "steps_yesterday": steps,
  "calories_burned": calories
}
```

Then in **iOS Automations**: Time of Day → 6:00 AM → run the Shortcut.

### Verify it's working

```
GET /health-sync/status
```

Returns the last sync date, source (`apple_watch` or `mock`), and key metrics.

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
| Health Data | Apple Watch via iOS Shortcut + HealthKit |
| Calendar | Google Calendar API (OAuth) |
| Backend | FastAPI + Python, deployed on Railway |
| Frontend | Vanilla JS, no build step |
| Scheduler | cron + iOS Automations |
