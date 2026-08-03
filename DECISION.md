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
**Status:** Accepted (reconfirmed 2026-08-03 — Supabase is the production DB)

**Context:** Need auth, Postgres, and storage without standing up infra day one. Local DX should work offline.

**Decision:** SQLAlchemy models talk to `DATABASE_URL`. Local default = SQLite. **Production = Supabase Postgres** (confirmed). Auth/Storage via Supabase when Week 3 lands. JobSpy pipeline upserts with `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. Schema: `backend/db/schema.sql` (greenfield) or migrations `001`+`002`.

**Consequences:**
- Slight SQLite vs Postgres divergence (JSON types, etc.) — keep queries portable.
- `create_all()` is fine for local; prod should apply SQL migration / migrate properly before launch.
- Agents need Supabase service-role credentials in `backend/.env` (never commit) to upsert scraped jobs.

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

## ADR-011 — Fresh-grad / internship discovery

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Many Haunsla seekers (including the founding user) are fresh graduates. Pure mid/senior remote feeds bury internships and junior roles.

**Decision:**
- Default `SCRAPE_ENTRY_LEVEL=1` adds internship / junior / graduate / entry-level search terms across Indeed, LinkedIn (short list), Google, and ATS career boards.
- Infer `experience_level` (`internship` | `entry` | `mid` | `senior`) from title/job_type first; avoid description-only “intern” matches (mentor-intern boilerplate).
- Expose `internship` in API filters and mobile Search chips alongside entry/mid/senior.

**Consequences:**
- Heuristics will mis-tag some roles; title signals are preferred and can be tightened over time.
- Fresh-grad volume still depends on source quality (Indeed job_type, ATS titles, WWR).

---

## ADR-012 — Pakistan city employer list (LHE / KHI / ISB)

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Fresh graduates need roles from major employers in Lahore, Karachi, and Islamabad — including banks and graduate trainee programs — not only worldwide remote boards. Many PK employers lack public Greenhouse/Ashby/Lever boards.

**Decision:**
- Maintain `config/pakistan_companies.json` (200+ employers across tech, business, marketing, finance, banks).
- Scrape via Indeed/Google city×field and per-company graduate/intern/trainee queries (`pakistan_companies.py`), plus ATS when `ats`+`slug` exist.
- Default `ALLOW_PAKISTAN_LOCAL=1` so on-site/hybrid PK city jobs are kept alongside remote.
- Document all toggles in `backend/SCRAPERS.md` for re-runs.

**Consequences:**
- Full company pass is Indeed-heavy; use `PK_COMPANY_LIMIT` / `HAUNSLA_SCRAPE_QUICK` for shorter runs.
- Grow the JSON over time; optional ATS slugs improve direct career-page coverage.

---

## ADR-013 — Remote ads for growth; internships for Pakistan grads

**Date:** 2026-08-03  
**Status:** Accepted

**Context:** Haunsla will mostly run **remote job ads** to acquire users. Many of those users — especially fresh graduates — also need normal/local roles: they have FYP projects, rarely have internships, and don’t know how to get a first job in tech/business/marketing/finance.

**Decision:**
- Keep **remote-first** as the brand and acquisition story (*Remote jobs. Real ambition.*).
- Keep scraping + filters for **internships / entry / trainee** and Pakistan city employers (ADR-011, ADR-012) so grads can find first steps without prior experience.
- Onboarding lets seekers pick Remote / Internships / First job so the feed isn’t only senior remote roles.
- Employer ads stay remote-heavy for monetization; seeker value includes local graduate discovery.

**Consequences:**
- Feed is mixed (remote + PK local) when `ALLOW_PAKISTAN_LOCAL=1`; Search chips + onboarding path keep UX clear.
- Do not turn Haunsla into a full Rozee clone — remote remains the hero; internships/first jobs are the fresh-grad lane.

---

## Pending decisions (not yet ADR’d)

- Employer portal framework (Next.js vs plain Flask templates)
- Exact JazzCash/EasyPaisa merchant integration path
- Whether seeker feed personalization is server-side or client-side first
- Primary deploy target: Railway vs Render
- App store legal entity / privacy policy hosting

When these are chosen, add ADR-014+.
