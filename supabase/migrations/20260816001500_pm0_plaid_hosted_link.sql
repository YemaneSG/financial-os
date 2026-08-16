create table private.pm0_plaid_link_sessions (
  session_id uuid primary key,
  owner_subject text not null
    references private.owner_authorizations (subject),
  link_token text not null unique,
  state text not null default 'pending',
  expires_at timestamptz not null,
  check_nonce uuid,
  check_started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default statement_timestamp(),
  constraint pm0_plaid_link_token_is_sandbox
    check (link_token like 'link-sandbox-%'),
  constraint pm0_plaid_link_state_is_known
    check (state in (
      'pending', 'checking', 'succeeded', 'cancelled', 'expired', 'failed'
    )),
  constraint pm0_plaid_link_expiry_is_bounded
    check (
      expires_at > created_at
      and expires_at <= created_at + interval '20 minutes'
    ),
  constraint pm0_plaid_link_claim_is_consistent
    check (
      (state = 'checking' and check_nonce is not null and check_started_at is not null)
      or
      (state <> 'checking' and check_nonce is null and check_started_at is null)
    ),
  constraint pm0_plaid_link_finish_is_consistent
    check (
      (state in ('succeeded', 'cancelled', 'expired', 'failed') and finished_at is not null)
      or
      (state in ('pending', 'checking') and finished_at is null)
    )
);

revoke all on table private.pm0_plaid_link_sessions
  from public, anon, authenticated, service_role;

create or replace function public.pm0_active_owner_subject()
returns text
language sql
stable
security invoker
set search_path = pg_catalog, public
as $$
  select case
    when public.pm0_is_active_firebase_owner()
      then nullif(auth.jwt() ->> 'sub', '')
    else null
  end;
$$;

revoke all on function public.pm0_active_owner_subject()
  from public, anon, service_role;
grant execute on function public.pm0_active_owner_subject()
  to authenticated;

create or replace function public.pm0_store_plaid_link_session(
  p_session_id uuid,
  p_owner_subject text,
  p_link_token text,
  p_expires_at timestamptz
)
returns boolean
language plpgsql
volatile
security definer
set search_path = pg_catalog, private
as $$
begin
  insert into private.pm0_plaid_link_sessions (
    session_id,
    owner_subject,
    link_token,
    expires_at
  )
  select
    p_session_id,
    owner.subject,
    p_link_token,
    p_expires_at
  from private.owner_authorizations as owner
  where owner.subject = p_owner_subject
    and owner.active;

  return found;
end;
$$;

create or replace function public.pm0_claim_plaid_link_session(
  p_session_id uuid,
  p_owner_subject text,
  p_claim_nonce uuid,
  p_now timestamptz
)
returns table (
  link_token text,
  state text,
  expires_at timestamptz,
  claimed boolean
)
language plpgsql
volatile
security definer
set search_path = pg_catalog, private
as $$
begin
  update private.pm0_plaid_link_sessions as session
  set
    state = 'expired',
    check_nonce = null,
    check_started_at = null,
    finished_at = p_now
  where session.session_id = p_session_id
    and session.owner_subject = p_owner_subject
    and session.state in ('pending', 'checking')
    and session.expires_at <= p_now;

  return query
  update private.pm0_plaid_link_sessions as session
  set
    state = 'checking',
    check_nonce = p_claim_nonce,
    check_started_at = p_now
  where session.session_id = p_session_id
    and session.owner_subject = p_owner_subject
    and session.expires_at > p_now
    and (
      session.state = 'pending'
      or (
        session.state = 'checking'
        and session.check_started_at <= p_now - interval '30 seconds'
      )
    )
  returning session.link_token, session.state, session.expires_at, true;

  if found then
    return;
  end if;

  return query
  select
    null::text,
    session.state,
    session.expires_at,
    false
  from private.pm0_plaid_link_sessions as session
  where session.session_id = p_session_id
    and session.owner_subject = p_owner_subject;
end;
$$;

create or replace function public.pm0_finish_plaid_link_session(
  p_session_id uuid,
  p_owner_subject text,
  p_claim_nonce uuid,
  p_state text,
  p_finished_at timestamptz
)
returns boolean
language plpgsql
volatile
security definer
set search_path = pg_catalog, private
as $$
declare
  changed_rows integer;
begin
  if p_state not in ('succeeded', 'cancelled', 'expired', 'failed') then
    return false;
  end if;

  update private.pm0_plaid_link_sessions as session
  set
    state = p_state,
    check_nonce = null,
    check_started_at = null,
    finished_at = p_finished_at
  where session.session_id = p_session_id
    and session.owner_subject = p_owner_subject
    and session.state = 'checking'
    and session.check_nonce = p_claim_nonce;

  get diagnostics changed_rows = row_count;
  return changed_rows = 1;
end;
$$;

create or replace function public.pm0_release_plaid_link_session(
  p_session_id uuid,
  p_owner_subject text,
  p_claim_nonce uuid
)
returns boolean
language plpgsql
volatile
security definer
set search_path = pg_catalog, private
as $$
declare
  changed_rows integer;
begin
  update private.pm0_plaid_link_sessions as session
  set
    state = 'pending',
    check_nonce = null,
    check_started_at = null
  where session.session_id = p_session_id
    and session.owner_subject = p_owner_subject
    and session.state = 'checking'
    and session.check_nonce = p_claim_nonce;

  get diagnostics changed_rows = row_count;
  return changed_rows = 1;
end;
$$;

revoke all on function public.pm0_store_plaid_link_session(uuid, text, text, timestamptz)
  from public, anon, authenticated;
revoke all on function public.pm0_claim_plaid_link_session(uuid, text, uuid, timestamptz)
  from public, anon, authenticated;
revoke all on function public.pm0_finish_plaid_link_session(uuid, text, uuid, text, timestamptz)
  from public, anon, authenticated;
revoke all on function public.pm0_release_plaid_link_session(uuid, text, uuid)
  from public, anon, authenticated;

grant execute on function public.pm0_store_plaid_link_session(uuid, text, text, timestamptz)
  to service_role;
grant execute on function public.pm0_claim_plaid_link_session(uuid, text, uuid, timestamptz)
  to service_role;
grant execute on function public.pm0_finish_plaid_link_session(uuid, text, uuid, text, timestamptz)
  to service_role;
grant execute on function public.pm0_release_plaid_link_session(uuid, text, uuid)
  to service_role;

comment on table private.pm0_plaid_link_sessions is
  'Short-lived PM-0 Sandbox Hosted Link sessions; no public or access token is stored.';
comment on function public.pm0_active_owner_subject() is
  'Returns the verified active Firebase owner subject to the caller-scoped Edge client.';
