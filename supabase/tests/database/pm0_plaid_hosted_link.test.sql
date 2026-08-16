begin;

create extension if not exists pgtap with schema extensions;

select plan(34);

insert into private.firebase_identity_providers (issuer, audience)
values (
  'https://securetoken.google.com/synthetic-project',
  'synthetic-project'
);

insert into private.owner_authorizations (subject, active, session_version)
values ('synthetic-owner', true, 7);

select has_table(
  'private',
  'pm0_plaid_link_sessions',
  'private Hosted Link session table exists'
);

select ok(
  not has_schema_privilege('authenticated', 'private', 'usage'),
  'authenticated cannot use the private schema'
);

select ok(
  not has_table_privilege(
    'authenticated',
    'private.pm0_plaid_link_sessions',
    'select'
  ),
  'authenticated cannot read Hosted Link tokens'
);

select ok(
  not has_table_privilege(
    'service_role',
    'private.pm0_plaid_link_sessions',
    'select'
  ),
  'service role must use the reviewed RPC boundary'
);

select ok(
  has_function_privilege(
    'authenticated',
    'public.pm0_active_owner_subject()',
    'execute'
  ),
  'authenticated may request the caller-scoped owner subject'
);

select ok(
  not has_function_privilege(
    'anon',
    'public.pm0_active_owner_subject()',
    'execute'
  ),
  'anonymous cannot request the owner subject'
);

select ok(
  not has_function_privilege(
    'service_role',
    'public.pm0_active_owner_subject()',
    'execute'
  ),
  'service role cannot substitute for caller authorization'
);

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is(
  public.pm0_active_owner_subject(),
  'synthetic-owner',
  'the exact active Firebase owner receives its subject'
);
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":6}',
  true
);
set local role authenticated;
select is(
  public.pm0_active_owner_subject(),
  null::text,
  'a stale owner token receives no subject'
);
reset role;

select ok(
  has_function_privilege(
    'service_role',
    'public.pm0_store_plaid_link_session(uuid,text,text,timestamptz)',
    'execute'
  ),
  'service role may store a session through the reviewed RPC'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.pm0_store_plaid_link_session(uuid,text,text,timestamptz)',
    'execute'
  ),
  'authenticated cannot store a session'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.pm0_claim_plaid_link_session(uuid,text,uuid,timestamptz)',
    'execute'
  ),
  'service role may claim a session through the reviewed RPC'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.pm0_claim_plaid_link_session(uuid,text,uuid,timestamptz)',
    'execute'
  ),
  'authenticated cannot claim a session'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.pm0_finish_plaid_link_session(uuid,text,uuid,text,timestamptz)',
    'execute'
  ),
  'service role may finish a session through the reviewed RPC'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.pm0_finish_plaid_link_session(uuid,text,uuid,text,timestamptz)',
    'execute'
  ),
  'authenticated cannot finish a session'
);

select ok(
  has_function_privilege(
    'service_role',
    'public.pm0_release_plaid_link_session(uuid,text,uuid)',
    'execute'
  ),
  'service role may release a session through the reviewed RPC'
);

select ok(
  not has_function_privilege(
    'authenticated',
    'public.pm0_release_plaid_link_session(uuid,text,uuid)',
    'execute'
  ),
  'authenticated cannot release a session'
);

select ok(
  public.pm0_store_plaid_link_session(
    '10000000-0000-4000-8000-000000000001',
    'synthetic-owner',
    'link-sandbox-synthetic-one',
    statement_timestamp() + interval '15 minutes'
  ),
  'an active owner session is stored'
);

select is(
  (select count(*) from private.pm0_plaid_link_sessions),
  1::bigint,
  'exactly one private session row is stored'
);

select is(
  (
    select count(*)
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000001',
      'synthetic-non-owner',
      '20000000-0000-4000-8000-000000000001',
      statement_timestamp()
    )
  ),
  0::bigint,
  'cross-subject claim reveals no session'
);

select ok(
  (
    select claimed and link_token = 'link-sandbox-synthetic-one'
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000001',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000002',
      statement_timestamp()
    )
  ),
  'the exact owner atomically claims its pending session'
);

select ok(
  (
    select not claimed and link_token is null and state = 'checking'
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000001',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000003',
      statement_timestamp()
    )
  ),
  'a duplicate concurrent claim receives no token'
);

select ok(
  not public.pm0_finish_plaid_link_session(
    '10000000-0000-4000-8000-000000000001',
    'synthetic-owner',
    '20000000-0000-4000-8000-000000000003',
    'succeeded',
    statement_timestamp()
  ),
  'a wrong claim nonce cannot finish the session'
);

select ok(
  public.pm0_finish_plaid_link_session(
    '10000000-0000-4000-8000-000000000001',
    'synthetic-owner',
    '20000000-0000-4000-8000-000000000002',
    'succeeded',
    statement_timestamp()
  ),
  'the exact claim can finish the session'
);

select ok(
  (
    select not claimed and link_token is null and state = 'succeeded'
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000001',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000004',
      statement_timestamp()
    )
  ),
  'a replay receives the terminal state without its token'
);

select ok(
  not public.pm0_release_plaid_link_session(
    '10000000-0000-4000-8000-000000000001',
    'synthetic-owner',
    '20000000-0000-4000-8000-000000000002'
  ),
  'a terminal session cannot be released back to pending'
);

select ok(
  public.pm0_store_plaid_link_session(
    '10000000-0000-4000-8000-000000000002',
    'synthetic-owner',
    'link-sandbox-synthetic-two',
    statement_timestamp() + interval '15 minutes'
  ),
  'a second pending session is stored'
);

select ok(
  (
    select claimed
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000002',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000005',
      statement_timestamp()
    )
  ),
  'the second session can be claimed'
);

select ok(
  public.pm0_release_plaid_link_session(
    '10000000-0000-4000-8000-000000000002',
    'synthetic-owner',
    '20000000-0000-4000-8000-000000000005'
  ),
  'an unfinished check releases its claim'
);

select ok(
  (
    select claimed
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000002',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000006',
      statement_timestamp()
    )
  ),
  'a released session can be polled again'
);

select ok(
  public.pm0_store_plaid_link_session(
    '10000000-0000-4000-8000-000000000003',
    'synthetic-owner',
    'link-sandbox-synthetic-three',
    statement_timestamp() + interval '1 minute'
  ),
  'a short-lived session is stored'
);

select ok(
  (
    select not claimed and link_token is null and state = 'expired'
    from public.pm0_claim_plaid_link_session(
      '10000000-0000-4000-8000-000000000003',
      'synthetic-owner',
      '20000000-0000-4000-8000-000000000007',
      statement_timestamp() + interval '2 minutes'
    )
  ),
  'an expired session becomes terminal without exposing its token'
);

select ok(
  not public.pm0_store_plaid_link_session(
    '10000000-0000-4000-8000-000000000004',
    'synthetic-non-owner',
    'link-sandbox-synthetic-four',
    statement_timestamp() + interval '15 minutes'
  ),
  'a missing owner cannot store a session'
);

update private.owner_authorizations
set active = false
where subject = 'synthetic-owner';

select ok(
  not public.pm0_store_plaid_link_session(
    '10000000-0000-4000-8000-000000000005',
    'synthetic-owner',
    'link-sandbox-synthetic-five',
    statement_timestamp() + interval '15 minutes'
  ),
  'an inactive owner cannot store a new session'
);

select * from finish();

rollback;
