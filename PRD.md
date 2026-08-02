# Haunsla (حوصلہ) — Product Requirements Document

**Remote Jobs. Real Ambition.**  
Version 1.0 | August 2026

---

## 1. Overview

### Product Summary
Haunsla is a mobile-first remote job discovery app for Pakistani job seekers. It combines a curated feed of remote-only job listings with a TikTok-style scroll UI, making job discovery fast, engaging, and relevant.

### Problem
Pakistani remote job seekers have no dedicated platform. Rozee.pk and Mustakbil are bloated with on-site, low-quality listings. LinkedIn is noisy and not Pakistan-optimized. There is no clean, mobile-first destination for Pakistanis looking for remote work from global and local employers.

### Solution
A scroll-feed mobile app (Expo/React Native) that surfaces remote-friendly job listings filtered for Pakistani talent — clean cards, fast browsing, zero friction to apply.

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

### Primary — Job Seeker
- Pakistani, aged 20–35
- Tech, design, marketing, customer support, writing backgrounds
- Looking for remote work: international companies or Pakistani remote-first employers
- Phone-first, low tolerance for clunky UX
- Currently using LinkedIn, Rozee, or Upwork

### Secondary — Employer / Recruiter
- Pakistani startups hiring remotely
- International companies open to Pakistani talent
- Recruiters posting on behalf of clients

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
- Filters: Category, Experience level, Job type, Salary range, Date posted

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
