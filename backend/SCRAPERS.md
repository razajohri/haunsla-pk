# Haunsla scrapers — how to run them later

**Product intent:** Run **remote job ads** to grow the app. Still scrape **internships / trainee / first jobs** (Pakistan cities + remote) so fresh graduates who only have an FYP can find a starting role.

All commands run from `backend/` with the venv active:

```bash
cd backend
source .venv/bin/activate   # or: .venv/bin/python …
cp .env.example .env        # fill Supabase keys when ready
```

Company lists live in config (edit anytime, re-run scrapers):

| File | Purpose |
|------|---------|
| `config/career_pages.json` | **Direct company career pages** (ATS slug and/or `careers_url`) |
| `config/pakistan_companies.json` | **257** employers in Lahore / Karachi / Islamabad — tech, business, marketing, finance, **banks** |
| `config/worldwide_companies.json` | Worldwide remote-friendly ATS career boards |
| `config/ats_companies.json` | Bulk Ashby / Greenhouse / Lever slugs |

---

## One-shot full refresh (recommended)

Scrapes every enabled source → `jobs_cache.pkl` → Supabase upsert → link validate:

```bash
.venv/bin/python scripts/update_jobs_cache.py
```

### Direct company career pages (recommended for quality apply links)

```bash
# All companies in config/career_pages.json (GitLab, 10Pearls, i2c, Tkxel, banks, …)
.venv/bin/python scripts/scrape_career_pages.py

# Faster smoke
HAUNSLA_SCRAPE_QUICK=1 CAREER_PAGE_LIMIT=15 \
  .venv/bin/python scripts/scrape_career_pages.py
```

### Pakistan-only employer pass (LHE / KHI / ISB + banks + grads)

```bash
# Full PK company list (can take a while — hundreds of Indeed queries)
SCRAPE_PAKISTAN_COMPANIES=1 \
ALLOW_PAKISTAN_LOCAL=1 \
.venv/bin/python scripts/scrape_pakistan_companies.py

# Faster smoke
HAUNSLA_SCRAPE_QUICK=1 PK_COMPANY_LIMIT=20 \
.venv/bin/python scripts/scrape_pakistan_companies.py
```

---

## Master toggles (`.env`)

| Env | Default | What it runs |
|-----|---------|----------------|
| `SCRAPE_PAKISTAN_COMPANIES` | `1` | PK city employers + graduate field terms + banks |
| `SCRAPE_PAKISTAN_GOOGLE` | `1` | Google Jobs for PK fresh-grad / bank / city queries |
| `ALLOW_PAKISTAN_LOCAL` | `1` | Keep Lahore/Karachi/Islamabad (not only remote) |
| `SCRAPE_ENTRY_LEVEL` | `1` | Intern / junior / graduate terms on Indeed/LinkedIn/ATS |
| `SCRAPE_CAREER_PAGES` | `1` | Direct career pages (`career_pages.json`) |
| `CAREER_PAGE_LIMIT` | `0` | Cap companies for career-page scrape (`0` = all) |
| `SCRAPE_CAREER_BOARDS` | `1` | `worldwide_companies.json` ATS boards |
| `SCRAPE_ATS_BULK` | `1` | Large Ashby/GH/Lever slug lists |
| `SCRAPE_REMOTE_BOARDS` | `1` | Jobicy, Himalayas, Arbeitnow (+ RemoteOK if enabled) |
| `SCRAPE_INDEED` | `1` | Indeed (Pakistan + optional intl remote) |
| `SCRAPE_INDEED_INTL` | `1` | Extra Indeed USA/UK/Canada remote |
| `SCRAPE_GOOGLE` | `1` | Google Jobs remote terms |
| `SCRAPE_LINKEDIN` | `1` | LinkedIn remote / entry terms |
| `SCRAPE_REPSTACK` | `1` | RepStack careers |
| `SCRAPE_BAYT_NAUKRI` | `0` | Bayt + Naukri (opt-in) |
| `SCRAPE_HIRING_CAFE` | `0` | hiring.cafe (opt-in) |
| `SCRAPE_REMOTEOK` | `0` | RemoteOK API (noisy; opt-in) |
| `WORLDWIDE_ONLY` | `0` | If `1`, drop country-locked remote |
| `HAUNSLA_SCRAPE_QUICK` | `0` | Tiny scrape for local smoke tests |
| `SKIP_LINK_VALIDATE` | `0` | Skip dead-link pass after upsert |

### Pakistan volume knobs

| Env | Default | Meaning |
|-----|---------|---------|
| `PK_COMPANY_LIMIT` | `0` (all) | Cap how many companies from the JSON to query; `20` for a short run |
| `PK_CITY_RESULTS_PER_QUERY` | `120` | Indeed results per city×field term |
| `PK_COMPANY_RESULTS_PER_QUERY` | `60` | Indeed results per company query |
| `PK_GOOGLE_RESULTS` | `80` | Google results per PK term |

---

## Scraper map (code → source)

| Module / script | Source |
|-----------------|--------|
| `career_page_scraper.py` | **Direct career pages** — ATS APIs + HTML/AJAX parsers |
| `scripts/scrape_career_pages.py` | Career pages only → merge cache |
| `pakistan_companies.py` | PK employers JSON + Indeed city/field + company + Google |
| `career_boards.py` | Worldwide company ATS career pages |
| `ats_scraper.py` + `ats_companies.py` | Bulk Ashby / Greenhouse / Lever |
| `remote_boards.py` | Jobicy, Himalayas, Arbeitnow, RemoteOK |
| `app/scrapers/remotive.py` | Remotive |
| `app/scrapers/weworkremotely.py` | We Work Remotely (multi-category RSS) |
| `scraper.py` (`scrape_indeed` / `google` / `linkedin`) | JobSpy aggregators |
| `repstack_scraper.py` | RepStack |
| `hiring_cafe_scraper.py` | hiring.cafe |
| `scripts/update_jobs_cache.py` | Orchestrates **all** enabled scrapers |
| `scripts/scrape_pakistan_companies.py` | PK employers only → merge into cache |
| `scripts/sync_jobs_to_supabase.py` | Push pickle/cache to Supabase |
| `scripts/validate_job_links.py` | Soft-deactivate dead apply URLs |
| `scripts/apply_schema.py` | Apply `db/schema.sql` to Postgres |

Orchestration entrypoint: `scraper.scrape_all()`.

---

## Add more companies later

Edit `config/pakistan_companies.json`:

```json
{
  "name": "New Co",
  "cities": ["Lahore", "Karachi"],
  "sectors": ["tech", "business"],
  "aliases": ["NewCo"],
  "ats": "greenhouse",
  "slug": "newco"
}
```

`ats` + `slug` are optional (only if they use Greenhouse / Ashby / Lever). Then re-run:

```bash
.venv/bin/python scripts/scrape_pakistan_companies.py
# or
.venv/bin/python scripts/update_jobs_cache.py
```

---

## Sync to Supabase (production)

```bash
# once
.venv/bin/python scripts/apply_schema.py

# after any scrape
.venv/bin/python scripts/sync_jobs_to_supabase.py
# or full path already inside update_jobs_cache.py
```

Needs `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (or `DATABASE_URL`) in `.env`.
