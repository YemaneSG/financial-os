# Execution Packet — Sprint 2C Premium Capture and Receipt Dashboard

**Status:** Owner approved locally; production release authorized
**Packet owner:** Yemane
**Operating/integration lead:** Codex
**Date:** August 16, 2026
**Implementation base:** `origin/main` at `a673b3e`
**Working branch:** `codex/production-receipt-dashboard`

## Outcome

The operating production receipt PWA retains its proven five-to-ten-second
capture flow while presenting a premium, calm visual experience and a live owner
dashboard that makes receipt ingestion visible.

## Scope

- Restyle the existing PWA with the approved premium light/sage visual language.
- Keep `Photograph receipt` as the dominant action and retain the photo-library
  fallback, ordered multi-photo draft, HEIC behavior, upload, retry, and durable
  acknowledgement semantics.
- Add an owner-only dashboard to the idle capture home using existing list and
  search APIs.
- Show total captured, processing, needs-review, failed, and recent-receipt
  states with honest loading, empty, error, and refresh behavior.
- Preserve all existing history, detail, correction, search, accessibility, and
  mobile behavior.

## Non-goals

- No backend, contract, database, migration, storage, extraction, authentication,
  infrastructure, or production-data change.
- No Plaid, Supabase, manual transactions, matching, analytics SDK, or LLM.
- No invented financial aggregate or synthetic data in the authenticated
  production dashboard.

## Acceptance evidence

1. Camera capture remains the first and strongest action at a phone viewport.
2. Dashboard totals come only from owner-scoped receipt APIs.
3. A dashboard failure never blocks receipt capture.
4. Existing receipt upload/durable-acknowledgement tests remain green.
5. New dashboard loading, success, empty, error, and refresh tests pass.
6. Frontend lint, type checking, unit tests, production build, private-data scan,
   and visual phone-size review pass before deployment.

## Approval

The owner explicitly directed the operating lead to update the current production
receipt capture and build its dashboard on August 16, 2026.

On August 16, 2026, the owner reviewed the exact React capture surface locally
with synthetic data, approved the premium layout and final copy, and explicitly
authorized the guarded production release. This approval does not authorize any
receipt-record rewrite, migration, deletion, or unrelated feature deployment.

### Approved capture copy

- Surface label: `Dollar Trail`
- Kicker: `Every purchase leaves a clue`
- Heading: `Follow the story behind every dollar.`
- Support: `Snap the receipt now. Build a financial memory you can search,
  review, and learn from.`

`Dollar Trail` is the approved label for this receipt-capture surface. It does
not execute the deferred repository, package, infrastructure, or full-product
DollarTrace rename in `DT-OPEN-001`.

## Local verification

| Gate | Result |
|---|---|
| Frontend type check | Pass |
| Frontend lint | Pass |
| Web component and unit tests | Pass — 168 tests in 15 files |
| Production PWA build and service worker | Pass |
| Private-data scan | Pass |
| Phone-size synthetic visual review | Pass |

No private-data mutation was performed during local verification. Publication
must pass the repository CI and guarded deployment workflow before this packet
is marked complete. Production status is recorded on GitHub PR `#21` and its
linked deployment run so this public packet does not embed private deployment
identifiers.
