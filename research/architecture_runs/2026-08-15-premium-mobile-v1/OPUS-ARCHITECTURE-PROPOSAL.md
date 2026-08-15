# Premium Mobile v1 — Opus Architecture Proposal

**Date:** 2026-08-15
**Source:** Claude Opus architecture pass, normalized by Codex against current
official documentation and the shared-conversation idea addendum
**Status:** Technically decision-ready; canonically blocked pending a separate-track
owner decision and bounded execution packet

## 1. Executive decision

Build one Angular/Capacitor mobile application that calls two independent HTTPS
backends:

1. the existing FastAPI receipt service, unchanged and authoritative for receipt
   evidence; and
2. a new Supabase project, authoritative for Plaid data, transaction/receipt
   match decisions, reflection exposures, owner labels, and later behavioral
   inferences.

Reuse the existing Firebase owner identity. Supabase's supported Firebase
third-party-auth integration verifies the same Firebase ID token used by the
receipt API. The mobile app presents one login, not separate Firebase and
Supabase sessions.

V1 contains no LLM-dependent product path and no green/yellow/red guidance.

## 2. Context

```text
Owner device
  Angular + Capacitor
      |
      |-- Firebase ID token --> Existing receipt API --> existing receipt DB/GCS
      |
      |-- Firebase ID token --> Supabase Data API / Edge Functions
                                      |
                                      |-- private Postgres schemas
                                      |-- Plaid Link/session functions
                                      |-- transaction synchronization
                                      `-- Plaid API
```

The receipt service and new application fail independently. Neither database is
joined directly, replicated, migrated, or dual-written in v1.

## 3. Architecture decisions

### D1. Two backends, no gateway

The client calls the existing receipt API and Supabase directly. Both verify the
same owner identity. A new gateway would add a deployable hop without improving
the single-owner boundary.

### D2. Firebase remains the identity authority

- Configure hosted Supabase Firebase third-party auth.
- Add the required Firebase custom `role: authenticated` claim to the allowlisted
  owner.
- Supply the current Firebase ID token through Supabase's `accessToken` callback.
- Store the Firebase JWT `sub` as **text**, not UUID. Firebase UIDs are arbitrary
  1–128-character strings.
- RLS reads `auth.jwt()->>'sub'` and checks an owner-subject allowlist held in a
  private, non-client-readable table.
- Hosted Supabase rejects tokens from unregistered Firebase projects before they
  reach the database; RLS still enforces the owner subject on every table.
- Do not commit the Firebase project ID, owner UID, or any real resource name.

The existing receipt service's authorization remains unchanged.

### D3. Supabase owns only new domains

Private/application schemas:

- `identity`: private owner-subject allowlist and session metadata;
- `plaid_private`: access tokens, item cursors, webhook state, and sync jobs;
- `finance`: accounts and normalized bank transactions;
- `matching`: candidates and append-only owner decisions;
- `reflect`: queue exposures, sessions, labels, and label history;
- `signals`: versioned inferred candidates only when a later bounded slice needs
  them. Guidance and outcome schemas are deferred rather than pre-created in v1.

Every client-readable table has RLS. Plaid access tokens and sync internals live
outside exposed schemas and are reachable only from server-side functions.

### D4. Plaid uses Hosted Link first

Capacitor is not an officially supported Plaid SDK target. Plaid now deprecates
in-process mobile WebView Link and recommends Hosted Link when an official native
SDK cannot be used.

V1 therefore opens Hosted Link through the platform authentication browser
(`ASWebAuthenticationSession` on iOS / Android Custom Tab) and returns through a
Capacitor deep link. This is the fastest provider-supported path. A small custom
Capacitor bridge to the official iOS and Android SDKs is deferred until Hosted
Link proves inadequate.

Server-side Edge Functions:

- create Link/Hosted-Link session;
- exchange the public token;
- run incremental `/transactions/sync`;
- receive and verify webhooks;
- disconnect an Item and destroy the persistent access token.

The initial sync, webhook-triggered sync, app-foreground/manual refresh, and a
low-frequency reconciliation schedule share one idempotent sync function.
Cursor advancement occurs only in the same database transaction as added,
modified, and removed row handling.

### D5. Receipt integration stays read-only

Generate a TypeScript client from the frozen existing OpenAPI contract. Consume
receipt list/search/detail and controlled evidence-image capabilities without
changing receipt storage or tables.

Supabase may hold only the opaque receipt identifier and minimal derived matching
facts needed for a candidate: purchase date, integer minor-unit total, currency,
and normalized merchant. It does not copy receipt text, line items, images, raw
model output, or signed download URLs.

### D6. Matching is deterministic and correctable

Candidate scoring uses exact/near amount, bounded date distance, currency, and
normalized-merchant similarity. The rule and weights are versioned. Re-running
the matcher may update system evidence but never overwrite an owner confirmation
or rejection.

### D7. Behavioral evidence is layered

Keep source facts, deterministic facts, inferred candidates, owner labels,
guidance, and outcomes distinct. Owner labels are versioned events, not mutable
truth fields.

V1 adds a first-class reflection-exposure event:

- subject reference and subject type;
- selection reason and queue-policy version;
- evidence-availability snapshot;
- shown/skipped/answered/dismissed outcome;
- randomized selection probability when applicable.

The queue mixes prioritized uncertain/decision-relevant items with representative
controls. Missing feedback is not a negative label.

### D8. Angular uses stable platform primitives

Use standalone Angular, router-level lazy features, Signals, RxJS, and
`HttpClient`. Do not make the current experimental TanStack Angular Query package
a v1 dependency. A thin query/cache service is sufficient at single-owner scale
and avoids patch-level breaking changes.

Feature boundaries:

- `shell` and native lifecycle/deep links;
- `auth`;
- `home`;
- `activity`;
- `reflect`;
- `connections-settings`;
- generated `receipt-client`;
- typed `supabase-client`;
- pure deterministic `matching` and `reflection` domain modules.

Swipe interactions always have visible, accessible buttons; skip and edit are
always available. Tokens, signed URLs, and private evidence are not persisted in
web storage or logs.

### D9. No LLM in v1

V1 arithmetic, synchronization, matching, reflection selection, and factual home
observations are deterministic. Plaid categories and later AI classifications are
candidates, never truth. An AI proxy and typed tool layer require a later ADR and
evaluation gate.

## 4. Minimum data concepts

Money is integer minor units plus ISO currency. Quantities or high-precision unit
prices use decimal numeric types.

- `owner_subjects(subject text primary key, active, session_version)` — private;
- `plaid_items` — private item ID, encrypted/server-only access credential,
  status, cursor, last sync;
- `accounts` — provider account ID, type/subtype, masked display, currency;
- `transactions` — provider ID, posted/pending lifecycle, amount minor units,
  merchant/category candidates, removed/superseded state;
- `webhook_events` and `sync_jobs` — idempotency and retry metadata only;
- `match_candidates` — transaction ID, receipt ID, score, rule version, evidence;
- `match_decision_events` — confirmed/rejected/unresolved owner history;
- `reflection_exposures` — sampling/provenance contract from D7;
- `reflection_sessions` — bounded UI session envelope;
- `label_events` — subject, axis, value, optional reason, prior-event reference;
- `signal_candidates` — future inference envelope with provenance, confidence
  band, and abstention reason;
Future `guidance_events` and `outcome_events` remain research concepts, not v1
tables or contracts.

## 5. Bounded implementation slices

### Proposed Slice 0 — auth and Hosted Link spike

This slice may begin only after the owner accepts the separate-track canonical
decision and its bounded execution packet.

- Synthetic hosted Supabase project trusts the Firebase token.
- Owner subject reads one protected row; a second synthetic subject and no token
  read none.
- Hosted Link opens and returns correctly on a real iPhone and Android emulator.
- Bundle scan contains no service-role, Plaid, Firebase Admin, or owner secrets.

**Stop:** if direct Firebase third-party auth or Hosted Link return cannot be
proven, resolve the fallback before building the shell.

### Slice 1 — installable shell and Plaid Sandbox activity

- Four areas: Home, Activity, Reflect, Connections/Settings.
- Firebase owner sign-in and session lifecycle.
- Plaid Sandbox connect, initial sync, pending/posted correctness, reconnect, and
  disconnect.
- Activity list with deterministic totals and sync health.

This is the first installable owner build.

### Slice 2 — receipt adapter

- Generated client from the existing OpenAPI contract.
- Receipt list/detail shown read-only inside Activity.
- Evidence image capabilities used ephemerally and never cached.

### Slice 3 — deterministic matching

- Generate versioned candidates.
- Owner confirms/rejects/unresolves.
- Re-run proves owner decisions are preserved.

### Slice 4 — reflection

- Reflection exposure, session, and label-event contracts.
- Queue mixes prioritized and representative items.
- One question per card, accessible non-swipe actions, skip, undo, and edit.
- Home shows factual reflection readiness and coverage.

### Slice 5 — owner live acceptance

- Plaid live/Trial credentials held server-side.
- Import the available owner history.
- Verify sync overlap, reconnect, backup/restore, export, and deletion.

### Slice 6 — private distribution polish

- TestFlight and Android internal build.
- Complete real-device accessibility, lifecycle, offline/error, privacy, and
  provider-disclosure checks.
- Friends-and-family remains disabled until a later multi-user packet.

## 6. Acceptance evidence

1. Owner and non-owner authorization tests at both backends.
2. Real-device Firebase and Hosted Link returns.
3. Webhook and foreground-sync overlap does not duplicate spend.
4. Removed and pending-to-posted transactions preserve auditable history.
5. Receipt detail renders without copying receipt content into Supabase.
6. Match regeneration never overwrites an owner decision.
7. Reflection labels remain editable and historical; skipped cards create no
   negative labels.
8. Representative-control exposures are queryable separately from prioritized
   exposures.
9. Client bundles and logs contain no prohibited data or server secrets.
10. The existing receipt collector remains operational throughout.

## 7. Rejected immediate alternatives

- receipt migration, replication, shared SQL, or dual-write;
- a second login experience;
- client-held Plaid access credentials;
- deprecated in-process Plaid WebView Link;
- a new API gateway;
- Redis, Kafka, a service mesh, or independent microservices;
- experimental Angular query-state dependencies for v1;
- AI matching, authoritative AI calculations, or pre-purchase guidance;
- native SwiftUI/Kotlin product rewrites;
- public registration or friends-and-family roles in the first packet.

## 8. Stop conditions

Stop and escalate if:

1. Firebase token claims cannot safely support hosted Supabase RLS.
2. Hosted Link cannot complete required institution OAuth on the target devices.
3. A required receipt capability needs a frozen-contract change.
4. Sync tests lose, double-count, or silently mutate a transaction.
5. Any Plaid/server credential or private financial evidence reaches the client,
   logs, repository, or public artifact.
6. Real-device behavior invalidates the Angular/Capacitor path.
7. Store review requires a material product or privacy change.

## 9. Stop statement

This proposal is sufficient for an architecture decision. The gate review found
that current repository authority still covers only the existing receipt product.
After a separate-track canonical decision, a premium-app security addendum, and
owner acceptance, proposed Slice 0 can become the first bounded execution packet.
No production resource, live credential, existing receipt contract, or real owner
data is changed by accepting the proposal.
