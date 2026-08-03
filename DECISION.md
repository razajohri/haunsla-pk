# DECISION.md — Architecture Decision Record

Log of lasting technical/product decisions for Haunsla.  
Newest entries at the top. Agents: append here when you change stack or core patterns.

Format: **ADR-XXX — Title** → Context → Decision → Consequences.

---

## ADR-001 — Monorepo with Expo + Flask

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Need a seeker mobile app and a scraping/API backend shipping in ~4 weeks. Team is small; forked mental model from `find_jobs_canada`-style Flask scrapers.

**Decision:** Single git repo with `mobile/` (Expo RN) and `backend/` (Flask). No Nest/FastAPI rewrite. No separate repos until scale demands it.

**Consequences:**
- One PR can ship API + UI together.
- Agents must know which package they are editing.
- Employer web portal can later live as `web/` in the same monorepo.

---

## ADR-002 — Supabase Postgres (prod) + SQLite (local)

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Need auth, Postgres, and storage without standing up infra day one. Local DX should work offline.

**Decision:** SQLAlchemy models talk to `DATABASE_URL`. Local default = SQLite. Production = Supabase Postgres. Auth/Storage via Supabase when Week 3 lands. SQL migration kept in `backend/migrations/`.

**Consequences:**
- Slight SQLite vs Postgres divergence (JSON types, etc.) — keep queries portable.
- `create_all()` is fine for local; prod should apply SQL migration / migrate properly before launch.

---

## ADR-003 — Flask blueprints + scraper upsert by `external_id`

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Multiple job sources will re-fetch the same postings. Need idempotent ingest.

**Decision:** Each scraped job has a stable `external_id` (`remotive-{id}`, `wwr-...`). Runner upserts create/update. Scrapers implement a shared `BaseScraper` / `ScrapedJob` contract.

**Consequences:**
- Easy to add Ashby/Greenhouse later.
- Dedup across sources is imperfect (same job, different IDs) — accept for MVP; improve post-MVP.

---

## ADR-004 — Apply is deep-link / external URL (not in-app apply)

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** In-app apply needs ATS integrations and compliance. MVP goal is discovery + conversion to existing posting.

**Decision:** Job detail **Apply** opens `apply_url` via `Linking`. No resume upload in MVP.

**Consequences:**
- Faster MVP, fewer legal/storage issues.
- Conversion tracking is weaker — measure via outbound taps later.

---

## ADR-005 — Mobile state: React Query + Zustand + FlashList

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Feed is infinite and network-bound; prefs (saved, onboarding, filters) are local until auth.

**Decision:**
- TanStack Query for server data
- Zustand (+ AsyncStorage) for client prefs
- FlashList for the feed

**Consequences:**
- Clear separation of server vs local state.
- After Supabase Auth, migrate saved jobs from local IDs to `/api/saved`.

---

## ADR-006 — Payments split: JazzCash/EasyPaisa (employers) vs RevenueCat (seekers)

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** PRD originally mentioned Stripe; Pakistan employers need local wallets. Seekers on iOS/Android need store-compliant IAP for subscriptions.

**Decision:**
- Employer listing fees → JazzCash + EasyPaisa (Week 4)
- Seeker premium (post-MVP) → RevenueCat
- Do not use Stripe for Pakistan wallet checkout in MVP

**Consequences:**
- Two payment stacks to maintain.
- Employer portal must handle PK payment flows + pending/paid states on `employer_listings`.

---

## ADR-007 — Featured jobs via `is_featured` flag + feed sort

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** $50 featured placement must pin listings without a separate feed index service.

**Decision:** `jobs.is_featured` boolean; list endpoint orders `is_featured DESC, posted_at DESC`. Employer payment success sets featured + `active_until`.

**Consequences:**
- Simple, works at MVP scale.
- Need a cron later to expire featured when `active_until` passes.

---

## ADR-008 — Design system: forest + paper + Fraunces/DM Sans

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Avoid generic AI SaaS look; brand must feel ambitious and local-aware.

**Decision:** Theme tokens in `mobile/src/theme.ts` — forest greens, warm paper background, Fraunces for display, DM Sans for UI. Brand name is hero-level on Feed/Onboarding.

**Consequences:**
- New screens should reuse tokens, not invent palettes.
- Dark mode deferred.

---

## ADR-009 — Dev user identity via `X-User-Id` (temporary)

**Date:** 2026-08-03  
**Status:** Temporary — replace in Week 3

**Context:** Saved jobs / alerts APIs need a user key before Auth is wired.

**Decision:** Accept `X-User-Id` header (or `user_id` query) for now.

**Consequences:**
- Useful for scaffolding; **not** production-safe.
- Week 3 must validate Supabase JWT and ignore forged headers.

---

## ADR-010 — JobSpy scrape → pickle → Supabase pipeline (from remotejobscanada.ca)

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Haunsla needs the same job supply stack as remotejobscanada.ca: JobSpy aggregators, ATS board scrapes, atomic pickle cache, chunked Supabase upsert on `source_key`, and dead-link soft-deactivation. Geography must be Pakistan + open international remote (looser than Canada).

**Decision:**
- Port the Canada playbook into `backend/` (`scraper.py`, `ats_location.py`, `ats_companies.py`, `data_store.py`, `scripts/*`, `db/schema.sql`).
- Use `python-jobspy` for Indeed/Google/(optional Bayt/Naukri). Implement Ashby/Greenhouse/Lever via public board APIs (`ats_scraper.py`) because public JobSpy lacks those boards.
- Keep Remotive/WWR as additional sources mapped into the same DataFrame shape.
- Upsert on `source_key`; serve Supabase first, then `jobs_cache.pkl`; map rows to the existing mobile JSON shape.
- Pakistan filter lives in `ats_location.is_pakistan_job_row` (reject US/EU-only; allow PK + worldwide/anywhere remote).

**Consequences:**
- Scrape ops are script-driven (`update_jobs_cache.py`) plus `POST /api/jobs/scrape`.
- Company coverage for ATS depends on `ats_companies.py` + `config/ats_companies.json` — grow the slug lists over time.
- Cross-source dedupe remains URL/`source_key` based (same job on two boards may still appear twice).

---

## Pending decisions (not yet ADR’d)

- Employer portal framework (Next.js vs plain Flask templates)
- Exact JazzCash/EasyPaisa merchant integration path
- Whether seeker feed personalization is server-side or client-side first
- Primary deploy target: Railway vs Render
- App store legal entity / privacy policy hosting

When these are chosen, add ADR-011+.
