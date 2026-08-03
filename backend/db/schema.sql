-- Haunsla JobSpy pipeline schema (Canada playbook shape + seeker tables)
-- Apply with: python scripts/apply_schema.py

create extension if not exists pg_trgm;

create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  source_key text unique,
  site text,
  title text not null,
  company text,
  location text,
  description text,
  compensation text,
  interval text,
  min_amount numeric,
  max_amount numeric,
  currency text default 'USD',
  job_type text,
  job_url text,
  job_url_direct text,
  date_posted timestamptz,
  is_active boolean default true,
  is_remote boolean default true,
  raw_payload jsonb default '{}'::jsonb,
  -- Haunsla mobile / employer extras (nullable for scraped rows)
  external_id text,
  apply_url text,
  category text,
  experience_level text,
  salary_min integer,
  salary_max integer,
  salary_currency text default 'USD',
  tags jsonb default '[]'::jsonb,
  source text,
  pakistan_friendly boolean default true,
  haunsla_score integer,
  is_featured boolean default false,
  company_logo text,
  posted_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create unique index if not exists idx_jobs_external_id on public.jobs (external_id)
  where external_id is not null;

create index if not exists idx_jobs_active_posted
  on public.jobs (is_active, date_posted desc nulls last);

create index if not exists idx_jobs_title_trgm on public.jobs using gin (title gin_trgm_ops);
create index if not exists idx_jobs_company_trgm on public.jobs using gin (company gin_trgm_ops);
create index if not exists idx_jobs_site on public.jobs (site);
create index if not exists idx_jobs_featured on public.jobs (is_featured);

create table if not exists public.scrape_runs (
  id bigserial primary key,
  status text not null,
  jobs_seen integer default 0,
  message text,
  created_at timestamptz default now()
);

create table if not exists public.user_profiles (
  id bigserial primary key,
  auth_user_id text unique not null,
  email text not null,
  full_name text,
  skills jsonb default '[]'::jsonb,
  experience_level text,
  preferred_categories jsonb default '[]'::jsonb,
  push_token text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.saved_jobs (
  id bigserial primary key,
  auth_user_id text not null,
  job_id uuid references public.jobs(id) on delete cascade,
  applied boolean default false,
  created_at timestamptz default now(),
  unique (auth_user_id, job_id)
);

create table if not exists public.job_alerts (
  id bigserial primary key,
  auth_user_id text not null,
  email text not null,
  keyword text,
  category text,
  push_enabled boolean default false,
  email_enabled boolean default true,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists public.employer_listings (
  id bigserial primary key,
  employer_email text not null,
  company_name text not null,
  job_id uuid references public.jobs(id),
  placement text default 'standard',
  price_cents integer default 2000,
  payment_provider text,
  payment_status text default 'pending',
  payment_ref text,
  active_until timestamptz,
  created_at timestamptz default now()
);
