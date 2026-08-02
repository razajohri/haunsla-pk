-- Haunsla schema (Supabase / PostgreSQL)
-- Apply via Supabase SQL editor when ready for production

create table if not exists jobs (
  id bigserial primary key,
  external_id text unique,
  title text not null,
  company text not null,
  company_logo text,
  description text not null default '',
  apply_url text not null,
  category text,
  experience_level text,
  job_type text,
  salary_min integer,
  salary_max integer,
  salary_currency text default 'USD',
  tags jsonb default '[]'::jsonb,
  source text,
  is_remote boolean default true,
  pakistan_friendly boolean default true,
  haunsla_score integer,
  is_featured boolean default false,
  posted_at timestamptz default now(),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_jobs_posted_at on jobs (posted_at desc);
create index if not exists idx_jobs_category on jobs (category);
create index if not exists idx_jobs_featured on jobs (is_featured);

create table if not exists user_profiles (
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

create table if not exists saved_jobs (
  id bigserial primary key,
  auth_user_id text not null,
  job_id bigint references jobs(id) on delete cascade,
  applied boolean default false,
  created_at timestamptz default now(),
  unique (auth_user_id, job_id)
);

create table if not exists job_alerts (
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

create table if not exists employer_listings (
  id bigserial primary key,
  employer_email text not null,
  company_name text not null,
  job_id bigint references jobs(id),
  placement text default 'standard',
  price_cents integer default 2000,
  payment_provider text,
  payment_status text default 'pending',
  payment_ref text,
  active_until timestamptz,
  created_at timestamptz default now()
);
