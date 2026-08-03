# Haunsla (حوصلہ) — Product Requirements Document

**Remote Jobs. Real Ambition.**  
Version 1.0 | August 2026

---

## 1. Overview

### Product Summary
Haunsla is a mobile-first job discovery app for Pakistani talent. **Growth hook = remote job ads** (worldwide + Pakistan-friendly). **Trust hook for fresh graduates = internships and first jobs** in Pakistan (Lahore / Karachi / Islamabad and remote), because many grads have FYP projects but no internship and no clear path into work.

### Problem
1. Pakistani remote job seekers have no dedicated, clean mobile destination — Rozee/Mustakbil are noisy; LinkedIn isn’t Pakistan-optimized.
2. Fresh graduates struggle even harder: they finish university with an FYP, little or no internship, and no idea how to land a first role in tech, business, marketing, or finance (including banks).

### Solution
A scroll-feed mobile app (Expo/React Native) that:
- Leads with **remote** listings to attract and retain users
- Also surfaces **internships, trainee, and entry-level** roles (remote + Pakistan city) so fresh grads can apply without already having “2 years experience”
- Keeps apply as a deep link — low friction, no fake ATS for MVP

### Platform
| Layer | Choice |
|-------|--------|
| Mobile | Expo React Native (iOS + Android) |
| Backend | Python / Flask |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth (email + Google) |
| Employer payments | JazzCash + EasyPaisa |
| Seeker premium (post-MVP) | RevenueCat |
| Hosting | Railway/Render (API), Expo EAS (mobile), Cloudflare (CDN/DNS) |

---

## 2. Goals

| Goal | Metric |
|------|--------|
| Launch MVP | Within 4 weeks |
| Job seeker signups | 1,000 in first 30 days |
| Daily active users | 200 DAU by month 2 |
| Employer listings | 50 paid posts in first 60 days |
| Revenue | First paid listing within 2 weeks of launch |

---

## 3. Target Users

### Primary — Remote job seeker (growth)
- Pakistani, aged 20–35
- Tech, design, marketing, support, writing, finance
- Wants remote work from global or Pakistan-friendly employers
- Discovers Haunsla via remote job ads / social

### Primary — Fresh graduate (retention & mission)
- Final-year / just graduated; often has an FYP but **no internship**
- Looking for internship, trainee, junior, or first full-time role in Pakistan or remote
- Fields: tech, business, marketing, finance, banking
- Needs a simple “where do I start?” path — not a noisy board

### Secondary — Employer / Recruiter
- Pakistani startups hiring remotely or in LHE/KHI/ISB
- Banks / corporates with graduate trainee programs
- International companies open to Pakistani talent

---

## 4. Core Features — MVP

### 4.1 Scroll Feed (Job Discovery)
- Infinite scroll of job cards
- Each card: title, company, salary range (if available), tags (Remote, type, category), time posted
- Smooth vertical scroll, mobile-optimized
- Pull to refresh
- Skeleton loaders while fetching

### 4.2 Job Detail Screen
- Full job description
- Company info + logo
- Apply button (deep link to original posting)
- Save job button
- Share job button

### 4.3 Search & Filters
- Keyword search
- Filters: Category, Experience level (**internship**, entry, mid, senior), Job type, Salary range, Date posted
- Onboarding path: Remote · Internships · First job — sets experience filter for fresh grads

### 4.4 Auth & Profiles
- Email + password signup
- Google OAuth
- Profile: name, skills, experience level, preferred categories
- Used to personalize feed over time

### 4.5 Saved Jobs
- Save any job to a personal list
- View and manage saved jobs
- Mark as applied

### 4.6 Job Alerts
- Alerts by keyword or category
- Email when matching jobs are posted
- Push notification (optional, user-controlled)

### 4.7 Employer Portal (Web)
- Separate web interface for employers
- Post a job listing
- Standard ($20) or Featured ($50) placement
- JazzCash / EasyPaisa payment
- Dashboard to manage active listings

---

## 5. Features — Post-MVP

- Video intro cards (30-sec culture clips)
- Haunsla Score (Pakistan-friendliness rating)
- Resume builder (PDF CV)
- Referral system
- Company profiles
- In-app apply for select employers
- Pakistani employer badges
- Salary insights for Pakistan market
- Job seeker premium via RevenueCat ($5/mo)

---

## 6. Screens & Navigation

```
App
├── Onboarding
│   ├── Splash
│   ├── Welcome
│   ├── Category picker (personalization)
│   └── Sign up / Log in
│
├── Bottom Tabs
│   ├── Feed (scroll feed — home)
│   ├── Search (search + filters)
│   ├── Saved (saved jobs list)
│   └── Profile (user profile + settings)
│
└── Modals / Stacks
    ├── Job Detail
    ├── Apply (webview or deep link)
    ├── Filter Sheet
    ├── Alert Setup
    └── Settings
```

---

## 7. Monetization

| Stream | Details | Price |
|--------|---------|-------|
| Standard job post | 30-day listing, standard placement | $20 |
| Featured job post | 30-day listing, pinned top of feed | $50 |
| Job seeker premium (future) | Unlimited alerts, profile boost, resume builder | $5/mo |
| Recruiter bundle (future) | 5 posts/month + analytics | $75/mo |

---

## 8. Success Metrics (Month 1)

| Metric | Target |
|--------|--------|
| App installs | 500+ |
| DAU | 100+ |
| Jobs in database | 1,000+ |
| Paid employer listings | 10+ |
| Email alert signups | 200+ |
| App Store rating | 4.0+ |

---

## 9. Risks

| Risk | Mitigation |
|------|------------|
| Not enough Pakistan-friendly remote jobs | Haunsla Score; seed local remote employers |
| Scraper blocking | Rotate UAs, delays, proxies if needed |
| Low employer adoption early | First 10 listings free |
| App Store rejection | Follow Expo EAS guidelines |
| Rozee copies the format | Move fast, build community moat |

---

## 10. Out of Scope (MVP)

- Video job cards
- In-app apply / ATS integration beyond deep links
- Full recruiter analytics suite
- Multi-language UI (English first; Urdu later)
- Desktop-native seeker app

---

*Haunsla — حوصلہ — Find your next opportunity.*
