# Premium Mobile — Security and Production Control Addendum

**Status:** Approved — Gate A revision 2 and owner approval complete
**Owner:** Yemane
**Date:** August 15, 2026
**Applies to:** Separate Angular/Capacitor, Supabase, and Plaid product track
**Does not modify:** Operating receipt-service controls or frozen contracts

## 1. Gate policy

These controls extend `docs/security/control-baseline.md`; they do not weaken it.
`MUST` controls are release-blocking for the premium-mobile scope that triggers
them. Slice 0 uses synthetic identities and Plaid Sandbox data only. No live bank
credential, real transaction, or owner reflection record may be processed until
the applicable live-data controls have evidence and explicit owner authority.

## 2. Data classes

| Data | Class | Handling floor |
|---|---|---|
| Plaid client secret and Item access token | Restricted credential | Server-side only; encrypted secret storage; never logs, client, repository, screenshots, or CI |
| Firebase ID/refresh token and owner subject | Restricted identity | Provider-managed client session; server verification; private allowlist; never repository evidence |
| Account identifier, mask, balance, transaction, merchant, amount | Private financial data | Owner-only RLS, encrypted transport/at rest, minimal local cache, sanitized logs |
| Receipt image/text/signed capability | Private evidence | Existing receipt API only; never persisted in Supabase or mobile caches |
| Reflection label, reason, regret/value outcome | Sensitive behavioral data | Owner-only, append-only history, export/deletion, no analytics SDK payload |
| Synthetic fixtures and opaque identifiers | Public development data | Must not reconstruct the owner or real activity |

## 3. Mandatory controls

| ID | MUST control | Required evidence |
|---|---|---|
| PM-IAM-01 | Firebase remains the identity authority unless the proof fails. One common predicate requires exact Firebase issuer and audience/project, `role=authenticated`, exact text `sub`, active private allowlist row, and matching token/row `session_version`. Supabase-native JWTs are denied even if their subject matches. | Missing, invalid, wrong-project, Supabase-native, valid-non-owner, disabled-owner, stale-version, and valid-owner tests against Data API and Edge Functions |
| PM-IAM-02 | Disabling or incrementing the private owner row must immediately deny an issued token. Firebase refresh-token revocation is also required but is not treated as immediate rejection of an existing ID token. Public signup and anonymous financial access stay disabled. | Old-token denial, refreshed-token success, revoked-session integration test, and provider runbook |
| PM-DB-01 | Revoke default access to private schemas, Vault views, synchronization tables, and administrative functions. Expose only reviewed RLS tables/views or narrowly scoped security-definer RPCs with pinned `search_path`. | Grant snapshot, Security Advisor review, and cross-owner negative tests |
| PM-EDGE-01 | Every owner-triggered Edge Function first evaluates the common owner predicate using the unchanged caller JWT. Firebase third-party tokens are verified through the registered Data API integration; the incompatible legacy Supabase-secret gateway check stays disabled. Verification errors fail closed. An administrative/server client may exist only after predicate success. The synthetic test subject is never added to the receipt API allowlist. | Hosted Link function authorization matrix, invalid-token failure, and service-role-before-auth negative test |
| PM-SECRET-01 | Plaid environment/client secrets use Supabase Edge Function project secrets. Each persistent Plaid Item access token uses Supabase Vault authenticated encryption; application tables store only the Vault secret UUID. Access to `vault.decrypted_secrets` is denied to client roles and limited to the reviewed server-side path. | Migration/grant test, client denial test, bundle scan, and secret-free logs |
| PM-SECRET-02 | Disconnect/revocation destroys or renders unusable the Plaid token, clears synchronization authority, and records only a privacy-safe audit event. Rotation and incident steps are documented. | Sandbox disconnect/reconnect test and runbook |
| PM-WEBHOOK-01 | Verify `Plaid-Verification` as ES256 using the environment-matched JWK from `/webhook_verification_key/get`; require an issued-at age of at most five minutes; compare the raw-body SHA-256 in constant time; reject failures before state change. | Valid, bad algorithm/signature/key/body, stale, and wrong-environment tests |
| PM-WEBHOOK-02 | Treat webhooks as duplicate, delayed, and out of order. Persist a bounded idempotency record before scheduling synchronization; return promptly; recover through polling/reconciliation when delivery is absent. | Duplicate/reorder/retry and missed-webhook recovery tests |
| PM-SYNC-01 | `/transactions/sync` applies added, modified, and removed rows and advances its cursor in one database transaction. Overlapping webhook, foreground, and scheduled runs cannot double-count spend. | Concurrency, failure-injection, pending-to-posted, removal, and replay tests |
| PM-MOBILE-01 | Do not persist Plaid credentials, service-role keys, receipt evidence, signed URLs, raw financial responses, or reflection reasons in logs, analytics, Capacitor Preferences, or general web caches. Private offline data requires a later explicit encrypted-storage design. | Built bundle, device storage, cache, and log inspection |
| PM-LOG-01 | Logs use privacy-safe allowlisted metadata only. They exclude request/response bodies, descriptions, amounts, account numbers/masks, labels/reasons, tokens, JWTs, and webhook bodies. | Automated log snapshots and incident-query review |
| PM-RECEIPT-01 | The premium app consumes the existing receipt API read-only. Supabase may store only an opaque receipt reference and minimal deterministic matching facts approved by the packet; it never stores receipt images, text, raw model output, or signed capabilities. | Data inventory and integration tests |
| PM-BACKUP-01 | Before live use, record the selected Supabase plan and recovery point. Pro-or-higher daily backup plus an initial restore smoke test is the default. A Free-plan exception requires an automated encrypted logical export, off-site retention, owner-approved RPO, and restore proof. PITR is optional until the accepted RPO requires it. | Plan/config record, backup evidence, and isolated restore report |
| PM-PRIV-01 | Provide owner disconnect, export, and deletion paths before calling live use complete. Destructive deletion requires explicit confirmation and preserves only legally/operationally required audit metadata. | Sandbox lifecycle test and owner runbook |
| PM-CICD-01 | Dependency, secret/private-data, lint, type, unit, integration, bundle, and platform build checks run for changed premium-mobile scope. CI receives only environment-scoped short-lived or secret-store credentials. | Required check evidence and repository scan |
| PM-DIST-01 | Distribution remains private and single-owner. Friends-and-family or public access requires tenant-bound authorization, onboarding/privacy updates, and a later approved packet. | Distribution configuration inspection |
| PM-SUPPLY-01 | Commit a frozen lockfile, pin supported Angular/Capacitor/Supabase majors, use minimal CI permissions, keep pull-request CI credential-free, and restrict external integration credentials to the approved environment. | Frozen install, dependency inventory/audit, workflow-permission review, and sanitized artifact/cache retention |
| PM-ENV-01 | Record development resource owner, region, synthetic-only purpose, billing ceiling/no-upgrade rule, cost-alert owner, and teardown/retention decision before creation. | Private resource register and privacy-safe configuration evidence |
| PM-NATIVE-01 | Current App Store evidence requires Xcode 26/iOS 26 SDK. PM-0B also requires an Android SDK/emulator. An obsolete local build may aid development but cannot satisfy release or native-return evidence. | Toolchain versions, current iOS build, real-iPhone return, Android build/emulator return |

## 4. Slice 0 proportional boundary

Slice 0 may create an isolated development Supabase project and use Plaid Sandbox
only after explicit owner authorization. It may register the existing Firebase
project with Supabase and set the minimum required custom claims on one dedicated
synthetic Firebase subject. Claim changes use private read-modify-write and
rollback; they may not alter the real owner or receipt API authorization. Evidence
uses opaque subjects and contains no real project ID, Firebase UID, Plaid
identifier, token, account data, or resource name.

PM-0A proves hosted RLS/Edge Function authorization and server/browser Hosted Link
session behavior. Its short-lived Link session is bound to the authenticated
subject. The callback is an untrusted UI wake-up and carries no reusable token.
Success comes from the exact server-held session through `/link/token/get`; PM-0A
stops before public-token exchange and creates no persistent Plaid access token.

PM-0B proves native build and callback behavior using Xcode 26 on a compatible
host plus an Android SDK/emulator. PM-0A may begin while that lane is prepared,
but Slice 0 is not complete until PM-0B passes on a real iPhone and the approved
Android target.

No production deployment, Plaid Trial/live access, real bank connection, owner
transaction import, analytics SDK, notification service, or friends-and-family
identity is part of Slice 0.

## 5. Stop conditions

Stop and return to the owner if:

- Firebase third-party tokens cannot enforce the exact owner boundary in every
  Supabase surface;
- Hosted Link cannot complete institution OAuth and return safely on target
  devices;
- Vault plaintext is reachable by a client role or appears in logs/backups
  without its required encryption key lifecycle;
- webhook verification requires accepting unverifiable or stale messages;
- safe work requires modifying the existing receipt product or a frozen contract;
- any real credential or private financial evidence appears in source, prompts,
  CI, screenshots, or public artifacts.
- a callback, link token, or Supabase-native JWT can bypass the exact owner/session
  predicate;
- the approved modern iOS/Android evidence lane cannot be provided.

## 6. Primary vendor evidence

- Supabase Firebase third-party auth:
  https://supabase.com/docs/guides/auth/third-party/overview
- Supabase Vault:
  https://supabase.com/docs/guides/database/vault
- Supabase production and backups:
  https://supabase.com/docs/guides/deployment/going-into-prod
  and https://supabase.com/docs/guides/platform/backups
- Plaid webhook verification:
  https://plaid.com/docs/api/webhooks/webhook-verification/
- Plaid webhook delivery behavior:
  https://plaid.com/docs/api/webhooks/

## 7. Approval

**Owner approval:** Yemane, August 15, 2026
**Conditions:** PM-0A synthetic/Sandbox boundary only; no live financial data, production deployment, receipt-product change, Plaid token exchange, persistent Plaid Item, or paid upgrade
**Live financial-data authority:** Not granted by this addendum
