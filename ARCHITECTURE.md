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
2. If pipeline store is enabled: Supabase `jobs` first, then `jobs_cache.pkl`
3. Else SQLAlchemy query (remote-only + filters; featured first)
4. Paginated JSON returned in the mobile `items` shape

### Scraper flow (JobSpy pipeline — primary)
```
scrape_all()  [scraper.py]
  ├─ ATS: Ashby / Greenhouse / Lever  (ats_scraper.py + company slugs)
  ├─ Indeed (PK remote + optional US remote → PK/worldwide filter)
  ├─ Google Jobs ("remote jobs Pakistan" / worldwide)
  ├─ Remotive / We Work Remotely (legacy boards, same row shape)
  └─ hiring.cafe (optional, SCRAPE_HIRING_CAFE=1)
         ↓
  ats_location.py filter + URL dedupe
         ↓
  jobs_cache.pkl  (atomic write)
         ↓
  dataframe_to_job_records() → upsert_jobs() → public.jobs (source_key)
         ↓
  validate_job_links.py (soft-deactivate dead URLs)
```

Commands (from `backend/`):
- `python scripts/update_jobs_cache.py` — full refresh
- `python scripts/sync_jobs_to_supabase.py` — pickle → Supabase only
- `python scripts/validate_job_links.py --workers 12 --prune-unknown-aggregators`
- `POST /api/jobs/scrape` — same pipeline via API (`{"legacy": true}` for Remotive/WWR-only)

### Auth model (current → target)
| Phase | Approach |
|-------|----------|
| Now | Local saved IDs in Zustand; API accepts `X-User-Id` header (dev) |
| Week 3 | Supabase Auth JWT; backend validates token; maps to `user_profiles` |

---

## 4. Data model (core)

```
jobs
  id, source_key (unique), site, title, company, location, description
  job_url / job_url_direct, apply_url, compensation, interval
  min_amount / max_amount / currency, job_type
  date_posted, is_active, is_remote, raw_payload
  # Haunsla extras:
  external_id, category, experience_level, tags[], pakistan_friendly
  is_featured, haunsla_score, posted_at, created_at, updated_at

scrape_runs
  id, status, jobs_seen, message, created_at

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

Greenfield Supabase: apply `backend/db/schema.sql`.  
Existing DB: also `backend/migrations/002_jobspy_pipeline.sql`.

Local: SQLite file via SQLAlchemy `create_all()` + optional `jobs_cache.pkl`.  
Prod: Supabase Postgres — apply `backend/db/schema.sql` (or 001 + 002 migrations).

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
