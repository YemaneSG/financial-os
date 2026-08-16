# Premium Mobile — System Architecture

**Status:** Approved — Gate A revision 2 and owner approval complete
**Date:** August 15, 2026
**Owner:** Yemane
**Scope:** Separate premium-mobile product only
**Research source:** `research/architecture_runs/2026-08-15-premium-mobile-v1/OPUS-ARCHITECTURE-PROPOSAL.md`

## 1. Decision

Build one Angular/Capacitor application that uses the same Firebase identity to
call two independent HTTPS backends:

1. the existing receipt API, unchanged and authoritative for receipt evidence;
2. a new Supabase project, authoritative only for Plaid-derived transaction data,
   deterministic match decisions, reflection exposures, and owner labels.

The systems are not joined directly, migrated, replicated, or dual-written. V1
has no LLM-dependent path and no green/yellow/red guidance.

## 2. Trust and deployment shape

```text
Angular/Capacitor owner client
  |-- Firebase ID token --> existing receipt API --> existing receipt storage
  |
  |-- Firebase ID token --> Supabase Data API / Edge Functions
                                  |-- private Postgres schemas and RLS
                                  |-- short-lived Hosted Link sessions
                                  |-- server-only Plaid credentials
                                  `-- Plaid API / Hosted Link
```

The existing receipt collector remains operational if the premium app or
Supabase fails. No premium-mobile execution packet may change a frozen receipt
contract without the existing delta protocol.

## 3. Identity and authorization

Firebase remains the identity authority unless PM-0A disproves the integration.
Firebase UIDs are stored as text.

One private database predicate defines an active owner. It requires all of:

- exact registered Firebase issuer and audience/project;
- JWT `role = authenticated`;
- exact text `sub` in the private owner allowlist;
- active owner row;
- token `session_version` equal to the private allowlist version.

Supabase-native Auth tokens fail the issuer/audience test even if their `sub`
matches. Every client-readable RLS policy and every owner-triggered Edge Function
uses the same predicate. An Edge Function first calls the predicate with the
caller's token; only then may its server-only path use administrative access.
The Edge gateway's legacy Supabase-secret JWT check stays disabled for these
functions because it cannot validate Firebase third-party tokens. The unchanged
caller bearer is instead verified by the registered Supabase Data API Firebase
integration before the shared predicate runs; any verification error fails closed.

PM-0 uses a dedicated synthetic Firebase test subject in the registered project.
That subject is never added to the receipt API allowlist. Firebase custom claims
are changed through read-modify-write because `setCustomUserClaims` replaces the
entire claim object. Prior state and rollback remain private.

Setting the private owner row inactive immediately denies an issued token.
Re-enabling increments `session_version`, so the old token remains denied. Firebase
refresh-token revocation is also performed, but is not treated as immediate denial
of an already-issued ID token.

## 4. Plaid Hosted Link

Capacitor is not a first-class Plaid SDK target, and in-process mobile WebViews are
not used. Hosted Link opens through the platform authentication browser.

The server creates a short-lived, single-use Hosted Link session bound to the
authenticated subject and stores its `link_token` only server-side. The mobile
completion callback is an untrusted UI wake-up signal. It contains no public
token, access token, Firebase token, or reusable authorization capability.

Success is determined server-side from the exact bound Link session using a
verified `SESSION_FINISHED` webhook or `/link/token/get`. PM-0A uses polling so it
does not need a production webhook. Forged, cross-subject, expired, duplicate,
and replayed returns cannot attach or exchange an Item.

PM-0 stops before public-token exchange and creates no persistent Plaid Item
access token. PM-1 introduces exchange, Vault storage, synchronization, webhook,
and disconnect behavior under its own packet.

## 5. Data ownership

Supabase private/application domains may later include:

- identity allowlist and session metadata;
- Plaid Items/cursors and transaction facts;
- opaque receipt references and minimal matching facts;
- append-only match decisions;
- reflection exposures, sessions, and multi-axis label events;
- versioned signal candidates only when an approved slice requires them.

Guidance/outcome tables, LLM persistence, event buses, Redis, and speculative
future schemas are not v1 infrastructure.

Money uses integer minor units plus ISO currency. Quantity and high-precision
unit price use decimal numeric types. Source facts, deterministic facts,
inferences, owner labels, and future guidance remain distinguishable.

## 6. Delivery gates

### PM-0A — Hosted authorization and browser/session proof

Executable on the current host after owner approval and Sandbox authority:

- Angular proof and locked dependency baseline;
- hosted Firebase-to-Supabase RLS/Edge Function authorization matrix;
- server-bound Plaid Sandbox Hosted Link creation;
- browser/session completion, cancel, expiry, cross-subject, and replay tests;
- no persistent Plaid Item or real financial data.

### PM-0B — Native build and device proof

Requires a modern host/runner capable of Xcode 26 plus Android tooling:

- current iOS build and real-iPhone Hosted Link return;
- Android build and emulator return;
- native console/storage/cache/callback privacy inspection;
- physical Android proof deferred to PM-1 private-owner exit.

PM-0A may start while the PM-0B lane is prepared. PM-0 is not complete until both
pass. A cloud compile alone does not replace real-iPhone callback evidence.

## 7. Toolchain constraint

The current host is Intel macOS 13.7.8 with Xcode 15.2 and no Android SDK. It can
perform web, database, RLS, Edge Function, and Hosted Link server/browser work but
cannot produce the current App Store-eligible iOS artifact. Apple requires Xcode
26/iOS 26 SDK for current uploads. The owner must authorize one modern build lane:
a newer Mac used directly, or a hosted Xcode 26 build/signing lane plus delivery
to a real iPhone for callback verification. Android SDK/emulator installation or
a hosted Android runner is also required.

## 8. Stop conditions

Stop if exact owner authorization cannot cover both Data API and Edge Functions;
Hosted Link requires a deprecated WebView or treats the callback as authority; a
secret/private value reaches the client, logs, source, or public evidence; current
native targets cannot be built; or any solution requires changing the receipt
collector or its frozen contracts.

## 9. Approval

**Owner approval:** Yemane, August 15, 2026
**Approved implementation boundary:** PM-0A only under the approved Slice 0 packet; PM-0B remains deferred pending its native toolchain/device lane
