create schema if not exists private;

revoke all on schema private from public, anon, authenticated;

create table private.firebase_identity_providers (
  issuer text primary key,
  audience text not null unique,
  enabled boolean not null default true,
  created_at timestamptz not null default statement_timestamp(),
  constraint firebase_issuer_matches_audience
    check (issuer = 'https://securetoken.google.com/' || audience),
  constraint firebase_audience_is_bounded
    check (length(audience) between 6 and 30)
);

create unique index one_enabled_firebase_identity_provider
  on private.firebase_identity_providers ((enabled))
  where enabled;

create table private.owner_authorizations (
  subject text primary key,
  active boolean not null default true,
  session_version bigint not null default 1,
  created_at timestamptz not null default statement_timestamp(),
  updated_at timestamptz not null default statement_timestamp(),
  constraint owner_subject_is_bounded
    check (length(subject) between 1 and 128),
  constraint owner_session_version_is_positive
    check (session_version > 0)
);

create unique index one_active_owner_authorization
  on private.owner_authorizations ((active))
  where active;

revoke all on table private.firebase_identity_providers from public, anon, authenticated;
revoke all on table private.owner_authorizations from public, anon, authenticated;
grant usage on schema private to service_role;
grant select, insert, update on table private.firebase_identity_providers to service_role;
grant select, insert, update on table private.owner_authorizations to service_role;

create or replace function public.pm0_is_active_firebase_owner()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  with token as (
    select coalesce(auth.jwt(), '{}'::jsonb) as claims
  )
  select coalesce(
    token.claims ->> 'role' = 'authenticated'
    and jsonb_typeof(token.claims -> 'aud') = 'string'
    and nullif(token.claims ->> 'sub', '') is not null
    and exists (
      select 1
      from private.firebase_identity_providers as provider
      join private.owner_authorizations as owner
        on owner.subject = token.claims ->> 'sub'
      where provider.enabled
        and provider.issuer = token.claims ->> 'iss'
        and provider.audience = token.claims ->> 'aud'
        and owner.active
        and owner.session_version = case
          when token.claims ->> 'session_version' ~ '^[1-9][0-9]{0,17}$'
            then (token.claims ->> 'session_version')::bigint
          else null
        end
    ),
    false
  )
  from token;
$$;

revoke all on function public.pm0_is_active_firebase_owner() from public, anon, service_role;
grant execute on function public.pm0_is_active_firebase_owner() to authenticated;

create table public.pm0_owner_probe (
  probe_key text primary key,
  message text not null,
  constraint pm0_probe_key_is_fixed
    check (probe_key = 'synthetic-proof')
);

insert into public.pm0_owner_probe (probe_key, message)
values ('synthetic-proof', 'PM-0A owner authorization is active.');

alter table public.pm0_owner_probe enable row level security;
alter table public.pm0_owner_probe force row level security;

revoke all on table public.pm0_owner_probe from public, anon, authenticated;
grant select on table public.pm0_owner_probe to authenticated;

create policy "authenticated role may request the PM0 proof"
  on public.pm0_owner_probe
  as permissive
  for select
  to authenticated
  using (true);

create policy "PM0 proof requires the exact active Firebase owner"
  on public.pm0_owner_probe
  as restrictive
  for select
  to authenticated
  using (public.pm0_is_active_firebase_owner());

comment on function public.pm0_is_active_firebase_owner() is
  'Fail-closed Firebase issuer, audience, role, subject, active, and session-version predicate for PM-0A.';

comment on table public.pm0_owner_probe is
  'One synthetic row used only to prove owner-bound RLS in PM-0A.';
