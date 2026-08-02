# TASKS.md — Haunsla Execution Backlog

Living checklist against the 4-week MVP.  
Agents: check items off when done; don’t invent parallel trackers.

**Legend:** `[x]` done · `[~]` in progress / partial · `[ ]` todo

---

## Week 0 — Foundation (now)

- [x] Monorepo scaffold (`mobile/`, `backend/`, docs)
- [x] Flask app factory, models, routes (jobs/saved/alerts/employers)
- [x] Demo job seed
- [x] Remotive scraper
- [x] We Work Remotely scraper
- [x] Expo app with tabs + onboarding + feed + detail + search + saved + profile
- [x] React Query feed + Zustand prefs + theme
- [x] Root docs: PRD, AGENTS, ARCHITECTURE, DECISION, TASKS
- [ ] Create GitHub remote + first push (manual — owner)
- [ ] Remove any secrets from working tree / rotate if leaked

---

## Week 1 — Backend hardens

- [~] Supabase credentials in `backend/.env` / `mobile/.env` (gitignored)
- [ ] Point `DATABASE_URL` at Haunsla Supabase project (direct host DNS failed locally — use pooler URI)
- [ ] Apply `backend/migrations/001_initial.sql` on the **Haunsla** Supabase project (not the other linked MCP project)
- [ ] Verify SQLAlchemy against Postgres (not only SQLite)
- [ ] Enable RLS + policies on Haunsla tables before exposing anon key broadly
- [ ] Schedule scrapers (APScheduler or platform cron)
- [ ] Add Ashby parser (high-value ATS)
- [ ] Pakistan-friendly heuristic filter (timezone / worldwide / PK keywords)
- [ ] Deploy API to Railway or Render
- [ ] Health check + scrape webhook secured with secret
- [ ] Seed / scrape until ≥ 200 real jobs in DB

### Scraper priority
| Source | Priority | Status |
|--------|----------|--------|
| Remotive | High | [x] |
| We Work Remotely | High | [x] |
| Wellfound | High | [ ] |
| LinkedIn Remote | High | [ ] |
| Ashby | Medium | [ ] |
| Greenhouse | Medium | [ ] |
| Lever | Medium | [ ] |
| Rozee.pk | Medium | [ ] |
| Jobillico | Low | [ ] |

---

## Week 2 — Mobile UI polish

- [~] Scroll feed with real API data (works; polish remaining)
- [x] Job detail (apply / save / share)
- [x] Search + filter screen
- [x] Bottom tab navigation
- [ ] Pull-to-refresh + empty/error states polish
- [ ] Filter sheet as modal (optional UX upgrade)
- [ ] Company logo images when URL present
- [ ] Loading / offline banners
- [ ] EAS project init (`eas.json`)
- [ ] App icon + splash final assets (brand)

---

## Week 3 — Auth + user features

- [ ] Supabase Auth: email + password
- [ ] Google OAuth
- [ ] SecureStore for session tokens
- [ ] Backend JWT validation (replace `X-User-Id` trust)
- [ ] `user_profiles` sync from auth
- [ ] Saved jobs via API (migrate off local-only IDs)
- [ ] Mark saved job as applied
- [ ] Job alerts CRUD in UI
- [ ] Email alerts via Resend when new matches scrape in
- [ ] Expo Notifications setup (opt-in push)
- [ ] Profile edit screen (name, skills, categories, experience)

---

## Week 4 — Employer + launch

- [ ] Employer web portal (`web/` or Flask templates)
- [ ] Post job form → `/api/employers/listings`
- [ ] JazzCash payment flow
- [ ] EasyPaisa payment flow
- [ ] Payment webhook → set `payment_status=paid`, toggle `is_featured`
- [ ] Expire featured listings when `active_until` passes
- [ ] First 10 employer listings free (promo flag)
- [ ] Privacy policy + terms pages
- [ ] App Store + Play Store listing copy
- [ ] EAS production builds
- [ ] Soft launch (TestFlight / internal testing track)

---

## Post-MVP (do not start until MVP soft-launched)

- [ ] Haunsla Score
- [ ] Video intro cards
- [ ] Resume builder
- [ ] Referral system
- [ ] Company profiles
- [ ] In-app apply
- [ ] Pakistani employer badges
- [ ] Salary insights
- [ ] RevenueCat seeker premium ($5/mo)
- [ ] Recruiter bundle ($75/mo)

---

## Bugs / debt

- [ ] Production CORS lockdown
- [ ] Rate-limit `/api/jobs/scrape`
- [ ] HTML description sanitization on detail (strip tags more carefully)
- [ ] Saved screen currently filters first page of feed only — switch to API when auth lands
- [ ] Add CI: backend pytest smoke + mobile `tsc --noEmit`

---

## Definition of Done — MVP soft launch

1. ≥ 500 remote jobs in production DB  
2. Feed / search / detail / save working for authenticated users  
3. At least one alert email path working  
4. Employer can pay for a listing (or free promo path live)  
5. Builds installable on iOS + Android internal tracks  

---

*Update this file as work completes. Prefer small vertical slices over big-bang rewrites.*
