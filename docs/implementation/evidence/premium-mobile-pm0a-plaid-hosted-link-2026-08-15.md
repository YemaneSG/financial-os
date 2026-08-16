# Premium Mobile PM-0A — Plaid Hosted Link Evidence

**Date:** August 15, 2026
**Issue:** `#18 — Prove Plaid Hosted Link session safety`
**Status:** Local/session boundary and hosted deployment complete; Sandbox credential/browser proof blocked on Plaid login
**Data boundary:** Synthetic identifiers and Plaid Sandbox only; no Item or financial data

## Current Plaid contract

- A standard Transactions Link token can use `user.client_user_id`; the newer
  `/user/create` requirement applies to specified user-based products and is not
  added to this bounded Transactions proof. See Plaid's
  [User API](https://plaid.com/docs/api/users/) and
  [Link API](https://plaid.com/docs/api/link/) documentation.
- Hosted Link is enabled by the `hosted_link` request object. The PM-0 request
  uses `is_mobile_app = true`, a custom-scheme completion redirect, and a
  15-minute URL lifetime. See
  [Hosted Link](https://plaid.com/docs/link/hosted-link/).
- The completion redirect is only a UI wake-up. It occurs on both success and
  exit, so `/link/token/get` remains the server-side source of truth.
- The server stores the `link_token` against the internal authenticated subject.
  Neither the Link token nor a public token is returned by the status endpoint.
- PM-0 does not call `/item/public_token/exchange` and cannot create a persistent
  Plaid Item or access token.

## Implemented boundary

- Added one private, short-lived Sandbox session table. Client roles and the
  service role have no direct table grant.
- Added a caller-scoped RPC that returns a subject only after the exact common
  Firebase owner predicate succeeds.
- Added service-role-only RPCs to store, atomically claim, finish, and release a
  session. A 30-second claim lease prevents concurrent duplicate polls and
  permits recovery after an interrupted function.
- Added `plaid-link-create` and `plaid-link-status` Edge Functions. The service
  role and Plaid clients are constructed only after caller authorization.
- Hosted Link create returns only `session_id`, `hosted_link_url`, and expiry.
  Status returns only `pending`, `succeeded`, `cancelled`, `expired`, or `failed`.
- `/link/token/get` result parsing reduces success/exit metadata immediately to a
  terminal state. Public tokens, account metadata, institution data, and Plaid
  response bodies are not persisted, returned, or logged.

## Verification

| Check | Result |
|---|---|
| Pure function/session suite | Pass — 22/22 |
| Database pgTAP suite | Pass — 34/34 |
| Existing owner authorization pgTAP suite | Pass — 26/26 |
| Database lint | Pass — no schema errors |
| Type check | Pass — pure handler and Edge runtime wiring |
| Wrong-subject/missing session | Pass — same 404, no Plaid call |
| Forged session identifier | Pass — 400 before server dependencies |
| Concurrent duplicate | Pass — pending, no second Plaid call or token |
| Terminal replay | Pass — stored state only, no Plaid call or token |
| Cancel and expiry | Pass — explicit terminal states |
| Plaid failure | Pass — claim released and fixed 503 response |
| Hosted migration smoke | Pass — 10/10, synthetic fixture removed |
| Hosted create function | Deployed; anonymous POST 401 and GET 405 |
| Hosted status function | Deployed; anonymous POST 401 and GET 405 |
| Legacy Supabase JWT gate | Disabled for both; Firebase trust remains caller-scoped through the Data API predicate |
| Receipt isolation | Existing receipt code, contracts, migrations, authorization, and infrastructure unchanged |

The dashboard deployment uses a mechanically bundled single-file copy of the
same source-controlled handler and runtime because the browser editor did not
submit a new multi-file function. Repository source remains split into reviewed
shared modules for maintainability; a later CLI deployment can use that layout.

## Remaining live evidence and blocker

The Plaid Dashboard is not authenticated in the available browser. No Sandbox
client ID or secret was available, so no secret was created, copied, or stored in
Supabase. The remaining PM-0A proof is:

1. owner signs in to the Plaid Dashboard;
2. Sandbox client ID and secret are added directly to Edge Function project
   secrets without entering source, chat, logs, or evidence;
3. a short-lived Hosted Link URL is created and completed/abandoned in Sandbox;
4. server polling proves success, cancel, expiry, duplicate, and replay against
   Plaid's live Sandbox response;
5. the test session is removed and secret/private-data scans are rerun.

This artifact does not claim full PM-0A or PM-0B completion.
