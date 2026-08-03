# AGENTS.md — Working in the Haunsla Repo

Instructions for AI coding agents (Cursor, Claude, Codex, etc.) contributing to this codebase.

---

## Mission

Build **Haunsla** — a mobile-first remote job discovery app for Pakistani talent.  
Tagline: *Remote Jobs. Real Ambition.*

Read these docs before large changes:
1. [PRD.md](./PRD.md) — what we’re building
2. [ARCHITECTURE.md](./ARCHITECTURE.md) — how it’s structured
3. [DECISION.md](./DECISION.md) — why choices were made
4. [TASKS.md](./TASKS.md) — current backlog / status

---

## Repo layout

```
haunsla/
├── mobile/          # Expo React Native app (seeker experience)
├── backend/         # Flask API + scrapers
├── docs/            # Extra product notes
├── PRD.md
├── ARCHITECTURE.md
├── DECISION.md
├── TASKS.md
└── AGENTS.md        # this file
```

Do **not** invent a second app structure. Extend what exists.

---

## Non-negotiables

1. **Pakistan-first remote jobs** — scrapers and filters must prefer remote + Pakistan-friendly roles.
2. **Mobile-first UX** — seeker product lives in Expo; keep the feed fast and uncluttered.
3. **No secrets in git** — never commit `.env`, Supabase keys, payment credentials, or passwords. Use `.env.example` only.
4. **Scope discipline** — ship MVP features from [TASKS.md](./TASKS.md) before post-MVP ideas (Haunsla Score, video cards, resume builder).
5. **Match existing patterns** — Flask blueprints + SQLAlchemy models; React Query + Zustand + FlashList on mobile.
6. **Don’t rewrite the stack** without a new entry in [DECISION.md](./DECISION.md).

---

## Where to change what

| Goal | Primary location |
|------|------------------|
| Job feed API / filters | `backend/app/routes/jobs.py`, `backend/data_store.py` |
| DB models / schema | `backend/app/models/`, `backend/migrations/`, `backend/db/schema.sql` |
| Scrapers (JobSpy pipeline) | `backend/scraper.py`, `ats_*.py`, `scripts/update_jobs_cache.py` |
| Scraper runbook | `backend/SCRAPERS.md` |
| PK employers (LHE/KHI/ISB + banks) | `backend/pakistan_companies.py`, `backend/config/pakistan_companies.json` |
| Legacy scrapers | `backend/app/scrapers/` (Remotive / WWR) |
| PK / worldwide geo filter | `backend/ats_location.py` |
| ATS company slugs | `backend/ats_companies.py`, `backend/config/ats_companies.json` |
| Demo / seed data | `backend/app/services/seed.py` |
| Feed UI | `mobile/src/screens/FeedScreen.tsx`, `JobCard.tsx` |
| Navigation | `mobile/src/navigation/` |
| Client API | `mobile/src/api/client.ts` |
| Local prefs / saved IDs | `mobile/src/store/appStore.ts` |
| Visual tokens | `mobile/src/theme.ts` |

---

## Coding standards

### Backend (Python / Flask)
- Keep routes thin; put scrape/upsert logic in scrapers/services.
- Prefer SQLAlchemy models already defined; add migrations SQL when schema changes.
- Local default DB is SQLite; production is Supabase Postgres via `DATABASE_URL`.
- Scrapers must be resilient: catch errors per source, don’t crash the whole run.
- Return JSON shapes the mobile client already expects (`items`, `page`, `has_next`, etc.).

### Mobile (Expo / TypeScript)
- Functional components + hooks.
- Data fetching via React Query; global UI prefs via Zustand.
- Use theme tokens from `src/theme.ts` (forest / paper palette) — no random purple AI defaults.
- Brand “Haunsla” / حوصلہ should remain a strong signal on Feed + Onboarding.
- Avoid cards-on-cards clutter; one clear job card pattern.
- Test against `EXPO_PUBLIC_API_URL` (LAN IP on physical devices).

### Docs
- When you finish a task, update [TASKS.md](./TASKS.md) checkboxes.
- When you make a lasting technical choice, append an ADR to [DECISION.md](./DECISION.md).

---

## Workflow for agents

1. Pick the next unchecked item in [TASKS.md](./TASKS.md) (or the user’s explicit ask).
2. Inspect existing code before writing new files.
3. Implement the smallest change that completes the task.
4. Smoke-test when possible:
   - Backend: `py -c "from app import create_app; ..."` or hit `/api/jobs`
   - Mobile: ensure TypeScript compiles / Expo starts
5. Update TASKS.md status.
6. Do **not** create git commits or push unless the user asks.

---

## Security reminders

- Treat anything in `.env` as secret.
- Employer payment integrations (JazzCash / EasyPaisa) must never log full payloads with PINs/credentials.
- User auth will use Supabase Auth — validate tokens server-side before trusting `X-User-Id` in production.
- Scrapers: polite rate limits, identifiable User-Agent (`HaunslaBot`).

---

## Design north star (mobile)

- One job per card, scroll-native discovery.
- Fast, calm, confident — forest green + warm paper, not generic SaaS purple.
- Expressive fonts already wired: **Fraunces** (display) + **DM Sans** (UI).
- First viewport of Feed = brand + feed. Don’t dump stats/promos into the hero.

---

## When stuck

- Prefer extending Remotive / WWR scrapers before adding low-priority sources.
- Prefer deep-link Apply over building in-app apply.
- Prefer email alerts before complex push infrastructure.
- Ask the user only when a decision changes product scope, pricing, or stack.
