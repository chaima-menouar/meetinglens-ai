-- MeetingLens AI durable Memory Vault
-- Run this in Supabase SQL Editor before enabling SUPABASE_URL/SUPABASE_SERVICE_KEY.
-- Safe to rerun when upgrading an existing MeetingLens table.

create table if not exists public.meetinglens_meetings (
    workspace_id text not null default 'default',
    meeting_id text not null,
    saved_at timestamptz not null default now(),
    payload jsonb not null,
    primary key (workspace_id, meeting_id)
);

-- Upgrade older installations that were created before workspace isolation.
alter table public.meetinglens_meetings
    add column if not exists workspace_id text not null default 'default';

-- Convert the old single-column primary key to a workspace-scoped key when needed.
do $$
begin
    if exists (
        select 1
        from pg_constraint
        where conrelid = 'public.meetinglens_meetings'::regclass
          and contype = 'p'
          and conname = 'meetinglens_meetings_pkey'
    ) then
        alter table public.meetinglens_meetings drop constraint meetinglens_meetings_pkey;
    end if;
exception when undefined_table then
    null;
end $$;

alter table public.meetinglens_meetings
    add constraint meetinglens_meetings_pkey primary key (workspace_id, meeting_id);

create index if not exists meetinglens_meetings_workspace_saved_at_idx
    on public.meetinglens_meetings (workspace_id, saved_at asc);

alter table public.meetinglens_meetings enable row level security;

-- No public/anon policies are created intentionally.
-- MeetingLens accesses this table server-side with the service-role key stored only
-- in Streamlit Secrets. Never expose that key in client-side code or commit it.
-- MEETINGLENS_WORKSPACE_ID scopes each deployment/workspace to its own rows.
