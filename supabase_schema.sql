-- MeetingLens AI durable Memory Vault
-- Run this once in Supabase SQL Editor before enabling SUPABASE_URL/SUPABASE_SERVICE_KEY.

create table if not exists public.meetinglens_meetings (
    meeting_id text primary key,
    saved_at timestamptz not null default now(),
    payload jsonb not null
);

create index if not exists meetinglens_meetings_saved_at_idx
    on public.meetinglens_meetings (saved_at asc);

alter table public.meetinglens_meetings enable row level security;

-- No public/anon policies are created intentionally.
-- MeetingLens accesses this table server-side with the service-role key stored only
-- in Streamlit Secrets. Never expose that key in client-side code or commit it.
