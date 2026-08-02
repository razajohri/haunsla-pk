# ARCHITECTURE.md — Haunsla System Design

Version 1.0 | August 2026

---

## 1. Big picture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│  Expo Mobile    │ ──────────────▶│  Flask API       │
│  (iOS/Android)  │◀────────────── │  (Railway/Render)│
└─────────────────┘                └────────┬─────────┘
                                            │
                     ┌──────────────────────┼──────────────────────┐
                     ▼                      ▼                      ▼
              ┌─────────────┐      ┌────────────────┐      ┌─────────────┐
              │  Supabase   │      │  Scrapers cron │      │  Email      │
              │  Postgres   │      │  Remotive/WWR… │      │  (Resend)   │
              │  Auth/Storage│     └────────────────┘      └─────────────┘
              └─────────────┘
                     ▲
┌─────────────────┐  │
│ Employer Web    │──┘  (Week 4 — posts + JazzCash/EasyPaisa)
│ Portal          │
└─────────────────┘
```

**Seeker path:** open app → scroll feed → open job → apply via external URL.  
**Supply path:** scrapers + paid employer listings → `jobs` table → API → feed.

---

## 2. Monorepo packages

| Package | Role | Runtime |
|---------|------|---------|
| `mobile/` | Job seeker app | Expo SDK 57, React Native |
| `backend/` | REST API, scrapers, seed | Flask + Gunicorn |
| Root docs | PRD, architecture, tasks, ADRs, agent rules | Markdown |

There is no shared TypeScript package yet. Mobile talks to backend over HTTP JSON.

---

## 3. Backend architecture

```
backend/
├── run.py / wsgi.py          # entrypoints
├── app/
│   ├── __init__.py           # create_app(), blueprints, seed
│   ├── config.py             # env-driven Config
│   ├── extensions.py         # SQLAlchemy db
│   ├── models/               # Job, SavedJob, JobAlert, …
│   ├── routes/               # health, jobs, saved, alerts, employers
│   ├── scrapers/             # Remotive, We Work Remotely, runner
│   └── services/             # seed_demo_jobs, (alerts later)
└── migrations/               # SQL for Supabase
```

### Request flow
1. Client hits `/api/jobs?...`
2. Route builds SQLAlchemy query (remote-only + filters)
3. Featured jobs ordered first, then `posted_at DESC`
4. Paginated JSON returned

### Scraper flow
1. `POST /api/jobs/scrape` or scheduled job calls `run_all_scrapers()`
2. Each scraper returns `ScrapedJob` dataclasses
3. Upsert by `external_id`
4. Commit per source; errors isolated per scraper

### Auth model (current → target)
| Phase | Approach |
|-------|----------|
| Now | Local saved IDs in Zustand; API accepts `X-User-Id` header (dev) |
| Week 3 | Supabase Auth JWT; backend validates token; maps to `user_profiles` |

---

## 4. Data model (core)

```
jobs
  id, external_id, title, company, description, apply_url
  category, experience_level, job_type
  salary_min/max/currency, tags[], source
  is_remote, pakistan_friendly, is_featured, haunsla_score
  posted_at, created_at, updated_at

user_profiles
  auth_user_id (Supabase UUID), email, skills[], preferred_categories[]

saved_jobs
  auth_user_id + job_id (unique), applied

job_alerts
  auth_user_id, email, keyword, category, push/email flags

employer_listings
  employer_email, company_name, job_id, placement, price_cents
  payment_provider, payment_status, active_until
```

Local: SQLite file via SQLAlchemy `create_all()`.  
Prod: Supabase Postgres — apply `backend/migrations/001_initial.sql`.

---

## 5. Mobile architecture

```
mobile/
├── App.tsx                   # fonts, QueryClient, navigator
└── src/
    ├── api/client.ts         # fetch wrapper → Flask
    ├── components/           # JobCard, skeletons
    ├── navigation/           # stack + bottom tabs
    ├── screens/              # Feed, Search, Saved, Profile, Detail, Onboarding
    ├── store/appStore.ts     # Zustand persist (onboarding, saved IDs, filters)
    ├── theme.ts              # colors / spacing / radius
    └── types/job.ts
```

### Navigation
- **Stack:** Onboarding XOR (MainTabs + JobDetail)
- **Tabs:** Feed | Search | Saved | Profile

### State
| Concern | Tool |
|---------|------|
| Server job data | TanStack React Query (infinite feed) |
| Filters / saved IDs / onboarding | Zustand + AsyncStorage |
| Auth tokens (Week 3) | Expo SecureStore |

### Feed performance
- `@shopify/flash-list` for the job list
- Page size 20, `onEndReached` → `fetchNextPage`
- Skeleton placeholders on first load

---

## 6. External systems

| System | Purpose | Status |
|--------|---------|--------|
| Remotive API | Remote job ingest | Implemented |
| We Work Remotely RSS | Remote job ingest | Implemented |
| Wellfound / LinkedIn / Rozee / ATS | More supply | Planned |
| Supabase | Postgres + Auth + Storage | Config ready, wire-up pending |
| Resend | Alert emails | Config stub |
| JazzCash / EasyPaisa | Employer checkout | Stub in employer route |
| RevenueCat | Seeker premium IAP | Post-MVP |
| Expo EAS | Builds + OTA | Not configured yet |
| Cloudflare | DNS / CDN | Ops later |

---

## 7. API surface (MVP)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Liveness |
| GET | `/api/jobs` | Feed + filters + pagination |
| GET | `/api/jobs/:id` | Detail + description |
| GET | `/api/jobs/meta/filters` | Enum metadata |
| POST | `/api/jobs/scrape` | Manual scrape trigger |
| GET/POST/PATCH/DELETE | `/api/saved` | Saved jobs (user header) |
| GET/POST/DELETE | `/api/alerts` | Alert CRUD |
| POST/GET | `/api/employers/listings` | Employer post + list |

---

## 8. Environments

| Env | API | DB | Mobile API URL |
|-----|-----|----|----------------|
| Local | `localhost:5000` | SQLite | `EXPO_PUBLIC_API_URL` |
| Staging | Railway/Render URL | Supabase | Staging URL |
| Production | Same host (or dedicated) | Supabase | Production URL |

CORS: `CORS_ORIGINS` env (default `*`). Tighten for production.

---

## 9. Security boundaries

- Secrets only in env / Supabase dashboard — never in repo.
- Scrapers do not store credentials.
- Apply links are external; we don’t proxy employer sites.
- Payment webhooks (Week 4) must verify signatures / merchant hashes.
- Replace trust-of-`X-User-Id` with JWT verification before launch.

---

## 10. Scaling notes (later)

- Move scrape schedule to APScheduler or platform cron, not request path.
- Add DB indexes already sketched in migration (`posted_at`, `category`, `is_featured`).
- Cache hot feed pages if needed (CDN or Redis) — not required for MVP.
- Featured listings: `is_featured=true` + `active_until` from employer payment.
