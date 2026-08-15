begin;

create extension if not exists pgtap with schema extensions;

select plan(26);

insert into private.firebase_identity_providers (issuer, audience)
values (
  'https://securetoken.google.com/synthetic-project',
  'synthetic-project'
);

insert into private.owner_authorizations (subject, active, session_version)
values ('synthetic-owner', true, 7);

select has_table('public', 'pm0_owner_probe', 'owner probe table exists');

select ok(
  (select relrowsecurity and relforcerowsecurity
   from pg_class
   where oid = 'public.pm0_owner_probe'::regclass),
  'owner probe has forced row-level security'
);

select ok(
  has_table_privilege('authenticated', 'public.pm0_owner_probe', 'select'),
  'authenticated has only a candidate SELECT grant'
);

select ok(
  not has_table_privilege('anon', 'public.pm0_owner_probe', 'select'),
  'anonymous cannot select the owner probe'
);

select ok(
  not has_schema_privilege('authenticated', 'private', 'usage'),
  'authenticated cannot use the private schema'
);

select ok(
  not has_table_privilege(
    'authenticated',
    'private.owner_authorizations',
    'select'
  ),
  'authenticated cannot read the private owner allowlist'
);

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is(
  (select count(*) from public.pm0_owner_probe),
  1::bigint,
  'the exact active Firebase owner reads one row'
);
reset role;

select set_config('request.jwt.claims', '{}', true);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'missing claims fail closed');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/wrong-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'wrong issuer is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"wrong-project","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'wrong audience is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"anon","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'wrong JWT role is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'missing subject is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-non-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'valid non-owner is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":6}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'stale session version is denied');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":"not-a-number"}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'malformed session version fails closed');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"http://127.0.0.1:54321/auth/v1","aud":"authenticated","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'Supabase-native JWT claims are denied');
reset role;

update private.owner_authorizations
set active = false,
    updated_at = statement_timestamp()
where subject = 'synthetic-owner';

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":7}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'inactive owner immediately denies an issued token');
reset role;

update private.owner_authorizations
set active = true,
    session_version = 8,
    updated_at = statement_timestamp()
where subject = 'synthetic-owner';

set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 0::bigint, 'reactivation does not revive the old token');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/synthetic-project","aud":"synthetic-project","role":"authenticated","sub":"synthetic-owner","session_version":8}',
  true
);
set local role authenticated;
select is((select count(*) from public.pm0_owner_probe), 1::bigint, 'refreshed token with the new version succeeds');
select ok(public.pm0_is_active_firebase_owner(), 'common owner RPC returns true for the valid owner');
reset role;

select set_config(
  'request.jwt.claims',
  '{"iss":"https://securetoken.google.com/other-project","aud":"other-project","role":"authenticated","sub":"synthetic-owner","session_version":8}',
  true
);
set local role authenticated;
select ok(not public.pm0_is_active_firebase_owner(), 'common owner RPC returns false for another project');
reset role;

select ok(
  not has_table_privilege('authenticated', 'public.pm0_owner_probe', 'insert'),
  'authenticated cannot insert probe rows'
);

select ok(
  not has_table_privilege('authenticated', 'public.pm0_owner_probe', 'update'),
  'authenticated cannot update probe rows'
);

select ok(
  not has_table_privilege('authenticated', 'public.pm0_owner_probe', 'delete'),
  'authenticated cannot delete probe rows'
);

select ok(
  not has_function_privilege(
    'anon',
    'public.pm0_is_active_firebase_owner()',
    'execute'
  ),
  'anonymous cannot execute the owner predicate RPC'
);

select ok(
  not has_function_privilege(
    'service_role',
    'public.pm0_is_active_firebase_owner()',
    'execute'
  ),
  'service role cannot substitute for caller authorization at the RPC boundary'
);

select * from finish();

rollback;
