# 🤖 Wellness Coach AI

> A conversational AI wellness coach that knows your health data and calendar — powered by Tavus CVI, ElevenLabs, and Claude.

## Demo Flow

1. App opens → Baymax greets you, already knowing your sleep score and HRV
2. You speak naturally: *"How am I doing today?"*
3. Baymax responds in real-time video: *"Your HRV is a bit low. Want me to guide you through a box breathing session?"*
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
│  ├── calendar_fetch.py  (gog CLI / mock)     │
│  ├── context_builder.py  (Claude API)        │
│  └── tavus_client.py  (Tavus CVI API)        │
└──────────────┬──────────────────────────────┘
               │
   ┌───────────┼───────────┐
   ▼           ▼           ▼
Anthropic    Tavus       Google Cal
(Claude)     (CVI)       (gog CLI)
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/AndreChuabio/wellness-coach
cd wellness-coach

# Backend
cd backend
pip install -r requirements.txt

# Copy env
cp .env.example .env
# Edit .env with your API keys
```

### 2. Set API Keys

Edit `.env`:
```
ANTHROPIC_API_KEY=...
TAVUS_API_KEY=...
TAVUS_REPLICA_ID=...
TAVUS_PERSONA_ID=...
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload
# → http://localhost:8000
```

### 4. Open Frontend

```bash
# Just open in browser (no build needed)
open frontend/index.html

# Or serve it:
cd frontend && python3 -m http.server 3000
# → http://localhost:3000
```

---

## Connecting Real Wearable Data

Edit `backend/health_mock.py` and replace `get_health_data()`:

### Oura Ring
```python
from health_mock import get_oura_health_data
data = get_oura_health_data(api_token="your_oura_token")
```
Get token: https://cloud.ouraring.com/personal-access-tokens

### Fitbit
```python
from health_mock import get_fitbit_health_data
data = get_fitbit_health_data(access_token="your_fitbit_token")
```
Get token: https://dev.fitbit.com

### Apple Health
Use [Health Auto Export](https://www.healthexportapp.com/) app → export JSON → parse in `health_mock.py`
Or use [Terra API](https://tryterra.co) as a unified wearable bridge.

---

## Cron Job (Morning Context Pre-build)

Pre-build the AI context at 6:30 AM so the session starts instantly:

```bash
# Test it
python3 cron/morning_context.py

# Add to crontab
crontab -e
30 6 * * * /usr/bin/python3 /path/to/wellness-coach/cron/morning_context.py
```

---

## Team Setup

1. Clone the repo
2. `cp .env.example .env` and fill in keys
3. `pip install -r backend/requirements.txt`
4. Run backend: `uvicorn main:app --reload` (from `backend/`)
5. Open `frontend/index.html`

**Teammate task split:**
- Frontend polish → `frontend/`
- Real wearable API → `backend/health_mock.py`
- Tavus persona setup → platform.tavus.io → add IDs to `.env`
- ElevenLabs voice → optional, Tavus has native voice

---

## Tech Stack

| Layer | Tech |
|---|---|
| Avatar + Video | [Tavus CVI](https://tavus.io) |
| Voice (optional) | [ElevenLabs](https://elevenlabs.io) |
| LLM Brain | [Claude](https://anthropic.com) (Haiku) |
| Calendar | `gog` CLI → Google Calendar |
| Backend | FastAPI + Python |
| Frontend | Vanilla JS, no build step |
| Scheduler | cron / OpenClaw cron |

---

Built at a hackathon. Ship it. 🚀
