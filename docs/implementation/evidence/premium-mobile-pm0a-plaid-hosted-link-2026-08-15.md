# Premium Mobile PM-0A — Plaid Hosted Link Evidence

**Date:** August 16, 2026
**Issue:** `#18 — Prove Plaid Hosted Link session safety`
**Status:** PM-0A server/browser proof complete; PM-0B native-device return remains open
**Data boundary:** Synthetic identifiers and Plaid Sandbox only; no real financial data, public-token exchange, or access token

## Current Plaid contract

- A standard Transactions Link token can use `user.client_user_id`; the newer
  `/user/create` requirement applies to specified user-based products and is not
  added to this bounded Transactions proof. See Plaid's
  [User API](https://plaid.com/docs/api/users/) and
  [Link API](https://plaid.com/docs/api/link/) documentation.
- Hosted Link is enabled by the `hosted_link` request object. The PM-0A
  server/browser proof uses `is_mobile_app = false`, a custom-scheme completion
  redirect, and a 15-minute URL lifetime. Plaid requires a separately registered
  HTTPS Universal/App Link when `is_mobile_app = true`; that native redirect and
  device-return proof remains in PM-0B. See
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
| Pure function/session suite | Pass — 23/23 |
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
| Live owner authorization | Pass — exact Firebase owner received 204 before create |
| Live Sandbox create | Pass — Hosted Link created with 201 in PM-0A browser mode |
| Live Sandbox success | Pass — two server polls returned `succeeded`; neither response contained a token |
| Live Sandbox cancellation | Pass — explicit exit followed by two `cancelled` polls; neither response contained a token |
| Hosted expiry transition | Pass — a third live-created session was advanced past expiry under a controlled database clock and returned `expired` twice without calling Plaid or returning a token |
| Credential handling | Pass with remediation — no value entered tracked source or evidence. A private terminal diagnostic briefly rendered the initial Sandbox secret; it was rotated, the replacement was verified directly and stored as an encrypted Edge Function secret, the old secret was revoked, and terminal/browser credential state was cleared |
| Synthetic cleanup | Pass — three private link-session rows and the synthetic owner row removed; two temporary Firebase users deleted; Email/Password provider disabled; temporarily enabled Identity Toolkit API disabled; temporary Firebase Authentication Admin binding removed and absence verified |
| Receipt isolation | Existing receipt code, contracts, migrations, authorization, and infrastructure unchanged |

The dashboard deployment uses a mechanically bundled single-file copy of the
same source-controlled handler and runtime because the browser editor did not
submit a new multi-file function. Repository source remains split into reviewed
shared modules for maintainability; a later CLI deployment can use that layout.
The rotated Plaid Sandbox credentials remain encrypted backend secrets because
the runtime needs them for subsequent synthetic development. All ephemeral users,
owner/session rows, URLs, tokens, terminal artifacts, and temporary cloud
permissions created for this proof were removed.

## Remaining PM-0B evidence

PM-0A does not claim native return readiness. PM-0B still requires:

1. an owner-controlled HTTPS Universal/App Link registered with Plaid;
2. `hosted_link.is_mobile_app = true` with that registered top-level
   `redirect_uri`;
3. real iOS and Android builds on supported toolchains; and
4. device-return evidence proving the custom/app link wakes the correct pending
   session while server polling remains the source of truth.

This artifact claims PM-0A completion only.
