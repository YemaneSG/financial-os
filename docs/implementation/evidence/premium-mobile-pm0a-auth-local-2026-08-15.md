# Premium Mobile PM-0A — Local Owner Authorization Evidence

**Date:** August 15, 2026
**Issue:** `#15 — Prove Firebase owner authorization through Supabase`
**Status:** Local policy and function-boundary evidence complete; hosted identity proof pending
**Data boundary:** Synthetic subjects and configuration only; no real identifiers or financial data

## Outcome

The new premium-mobile Supabase boundary now has one common, fail-closed owner
predicate. It requires an exact enabled Firebase issuer/audience pair, the
`authenticated` role, a non-empty subject, an active owner allowlist entry, and
the current positive session version. The same predicate controls the proof
table through restrictive row-level security and the Edge Function through a
caller-scoped RPC. The Edge Function never creates an admin or service-role
client.

No provider or owner rows are seeded by the migration. Private hosted values
must be provisioned out of band in the approved isolated development project.

## Local verification

| Check | Result |
|---|---|
| Database migration on clean local Supabase/Postgres 17 | Pass |
| Supabase database lint at warning level | Pass — no schema errors |
| pgTAP authorization matrix | Pass — 26 of 26 |
| Edge authorization boundary unit tests | Pass — 6 of 6 |
| Exact active Firebase owner | Reads the one synthetic proof row and predicate returns true |
| Missing or malformed claims | Denied |
| Wrong issuer, audience, role, or subject | Denied |
| Valid non-owner | Denied |
| Supabase-native JWT shape | Denied |
| Stale or malformed session version | Denied |
| Owner deactivation | Previously issued synthetic token is denied immediately |
| Version increment | Old token remains denied; refreshed matching version succeeds |
| Anonymous access and DML | Denied |
| Private schema/allowlist access by client roles | Denied |
| Service-role substitution at owner RPC boundary | Denied |
| Edge predicate error | Fails closed with a fixed response and no internal detail |
| Receipt protected-path diff | Pass — no changes |

## Test-environment note

Docker Desktop on this Intel macOS 13 host refuses the Supabase CLI bind mount
for the repository test directory. The migration itself starts and applies
normally. To preserve the exact pgTAP test, the unchanged SQL test file was
copied into the already-running local database container and executed there;
all 26 assertions passed. The Edge Runtime is disabled only in local CLI
configuration because the same host refuses its source bind mount. Pure boundary
tests run in credential-free CI, and the complete function/Data API matrix must
still be repeated against the approved hosted development project.

## Remaining hosted evidence

- Privately select or create the isolated development Supabase project and
  record owner, U.S. region, synthetic-only purpose, billing ceiling, and
  keep/delete decision outside the repository.
- Register the Firebase project as a trusted third-party identity provider
  without committing its identifier.
- Create or select one dedicated synthetic Firebase subject, apply only the
  bounded custom claims, force token refresh, and run the full Data API and Edge
  Function negative matrix.
- Prove provider revocation and roll back the synthetic subject claims.

This artifact completes the credential-free/local portion of issue #15. It does
not claim hosted Firebase signature verification, hosted RLS, or PM-0A completion.
