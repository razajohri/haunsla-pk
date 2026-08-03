# Haunsla (حوصلہ)

**Remote Jobs. Real Ambition.**

Mobile-first remote job discovery for Pakistani talent — TikTok-style scroll feed, curated remote listings, zero friction to apply.

## Monorepo

```
haunsla/
├── mobile/     # Expo React Native (iOS + Android)
├── backend/    # Flask API + scrapers
└── docs/       # Product docs
```

## Quick start

### 1. Backend

```bash
cd backend
py -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
py run.py
```

API runs at `http://localhost:5000`. Demo jobs are seeded automatically.

**Job supply pipeline** (same shape as remotejobscanada.ca, PK/worldwide geo):

```bash
cd backend
# Full refresh: ATS + Indeed + Google (+ Remotive/WWR) → pickle → Supabase → link check
python scripts/update_jobs_cache.py

# Or cache → Supabase only
python scripts/sync_jobs_to_supabase.py

# Apply Canada-shaped schema on Supabase/Postgres
python scripts/apply_schema.py
```

Set `HAUNSLA_SCRAPE_QUICK=1` for smaller local smoke runs. ATS company slugs live in `backend/config/ats_companies.json`.

Key endpoints:
- `GET /api/jobs` — feed / search / filters (Supabase → pickle → SQLAlchemy)
- `GET /api/jobs/:id` — job detail
- `POST /api/jobs/scrape` — JobSpy PK pipeline (`{"legacy": true}` for Remotive/WWR only)
- `GET|POST /api/saved` — saved jobs
- `GET|POST /api/alerts` — job alerts
- `POST /api/employers/listings` — employer posts

### 2. Mobile

```bash
cd mobile
npm install
npx expo start
```

Set `EXPO_PUBLIC_API_URL` in `mobile/.env` (defaults to `http://localhost:5000`).
On a physical device, use your machine's LAN IP instead of localhost.

## Stack

| Layer | Tech |
|-------|------|
| Mobile | Expo, React Navigation, React Query, Zustand, FlashList |
| Backend | Flask, SQLAlchemy, JobSpy pipeline, ATS scrapers |
| DB | SQLite (local) → Supabase PostgreSQL (prod) + `jobs_cache.pkl` |
| Payments | JazzCash / EasyPaisa (employer), RevenueCat (premium — later) |

## MVP roadmap

- **Week 1** — Backend schema + scrapers + deploy
- **Week 2** — Feed, detail, search, tabs
- **Week 3** — Auth, saved jobs, alerts
- **Week 4** — Employer portal + payments + store submit

---

## Docs

| Doc | Purpose |
|-----|---------|
| [PRD.md](./PRD.md) | Product requirements |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design |
| [TASKS.md](./TASKS.md) | Execution backlog |
| [DECISION.md](./DECISION.md) | Architecture decisions |
| [AGENTS.md](./AGENTS.md) | How AI agents should work in this repo |

Supabase keys live in `backend/.env` / `mobile/.env` (gitignored) — never in this file.

---

*Haunsla — حوصلہ — Find your next opportunity.*