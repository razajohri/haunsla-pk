-- Evolve existing Haunsla jobs table toward Canada JobSpy pipeline shape.
-- Safe to run on SQLite-exported Postgres or after 001_initial.sql.
-- For greenfield Supabase, prefer db/schema.sql.

alter table jobs add column if not exists source_key text;
alter table jobs add column if not exists site text;
alter table jobs add column if not exists location text;
alter table jobs add column if not exists job_url text;
alter table jobs add column if not exists job_url_direct text;
alter table jobs add column if not exists compensation text;
alter table jobs add column if not exists pay_interval text;
alter table jobs add column if not exists is_active boolean default true;
alter table jobs add column if not exists raw_payload jsonb default '{}'::jsonb;

create unique index if not exists idx_jobs_source_key on jobs (source_key)
  where source_key is not null;

create index if not exists idx_jobs_is_active on jobs (is_active);

create table if not exists scrape_runs (
  id bigserial primary key,
  status text not null,
  jobs_seen integer default 0,
  message text,
  created_at timestamptz default now()
);
