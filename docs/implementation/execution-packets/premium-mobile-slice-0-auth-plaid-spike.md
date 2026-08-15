# Execution Packet — Premium Mobile Slice 0 Auth and Plaid Path Proof

**Status:** Approved for PM-0A implementation; PM-0B deferred
**Packet owner:** Yemane
**Operating/integration lead:** Codex
**Implementation lead:** Codex for PM-0A unless Claude Code is reauthenticated and explicitly assigned
**Date:** August 15, 2026
**Implementation base:** `origin/main` at `94ba2c4`
**Working branch:** `codex/premium-mobile-bootstrap`

## 1. Outcome

PM-0 is divided so native-toolchain provisioning cannot stall the immediately
executable architecture proof:

> **PM-0A:** an Angular proof uses a dedicated synthetic Firebase subject to
> access exactly one Supabase row, denies every unauthorized case, and proves a
> subject-bound Plaid Sandbox Hosted Link server/browser session.
>
> **PM-0B:** the same proof builds with current native toolchains and completes
> safe Hosted Link return on a real iPhone and Android emulator.

PM-0A can start after approval while PM-0B's modern host is prepared. PM-0 is not
complete until both pass.

## 2. Why now

Firebase-to-Supabase authorization and the Capacitor Hosted Link return are the
two assumptions most capable of invalidating the stack. Proving the hosted
authorization/session design first is smaller and safer than building product
screens or importing transactions.

## 3. Canonical inputs

Read completely before planning:

- `AGENTS.md`
- `docs/product/premium-mobile-app-PRD.md`
- `docs/product/open-items-and-decisions.md` — DT-DEC-005 and DT-DEC-006
- `docs/product/roadmap.md` — Premium mobile track PM-0
- `docs/architecture/premium-mobile-system-architecture.md`
- `docs/security/control-baseline.md`
- `docs/security/premium-mobile-control-addendum.md`
- `docs/security/premium-mobile-threat-model.md`
- `docs/governance/ai-development-operating-model.md`

Research provenance remains available in:

- `research/architecture_runs/2026-08-15-premium-mobile-v1/OPUS-ARCHITECTURE-PROPOSAL.md`
- `research/architecture_runs/2026-08-15-premium-mobile-v1/CODEX-ARCHITECTURE-GATE-REVIEW.md`

Conversation history is supporting context only.

## 4. Accepted decisions

- The new application is separate from the operating receipt collector.
- Angular and Capacitor are the client baseline.
- Supabase owns only new premium-mobile domains.
- Firebase remains the preferred identity authority; failure of PM-0A triggers a
  deliberate fallback decision.
- Plaid Hosted Link is the first Capacitor path; no in-process WebView is allowed.
- Slice 0 uses one dedicated synthetic Firebase subject and Plaid Sandbox only.
- The synthetic subject is never authorized by the receipt API.
- PM-0 stops before public-token exchange and creates no persistent Plaid Item.

## 5. Scope

### PM-0A — immediately executable after approval

- Initialize isolated `apps/mobile/` Angular proof code with Capacitor
  configuration and no premium product styling.
- Initialize `supabase/` configuration, migration, Edge Function boundary, and
  tests for the new track.
- Configure one owner-authorized development Supabase project to trust the
  existing Firebase project without committing either identifier.
- Apply the minimum Firebase custom claims to one dedicated synthetic subject
  using private read-modify-write and rollback. Do not mutate the real owner.
- Prove exact Firebase issuer/audience, `authenticated` role, text `sub`, active
  allowlist, token-bound session version, RLS, Edge Function authorization,
  refresh, immediate invalidation, and receipt-allowlist isolation.
- Deny missing, malformed, wrong-project, Supabase-native, valid-non-owner,
  inactive-owner, stale-version, and revoked-session cases.
- Create a short-lived, single-use Plaid Sandbox Hosted Link session bound to the
  authenticated subject. Prove browser completion, cancel, expiry, wrong-subject,
  forged, duplicate, and replay behavior through `/link/token/get`.
- Treat a completion redirect only as an untrusted UI wake-up signal. It carries
  no reusable token and cannot attach or exchange an Item.
- Add privacy-safe deterministic tests, dependency/bundle/private-data scans, and
  a dated PM-0A handback.

### PM-0B — modern native build/device gate

- Use a compatible Xcode 26 host/runner to build the iOS target and verify Hosted
  Link return on a real iPhone.
- Install/authorize Android SDK tooling or use a hosted runner, build Android, and
  verify return on an emulator. Physical Android proof is a PM-1 exit gate.
- Inspect native console, crash output, navigation state, Capacitor Preferences,
  web cache, screenshots, bundle, and CI artifacts for callback/credential leaks.

## 6. Non-goals

- No Plaid Trial/live credentials, real bank connection, or real transactions
- No public-token exchange, persistent Plaid Item/access token,
  `/transactions/sync`, production webhook, account/activity UI, or financial
  schema beyond the minimum synthetic proof
- No receipt API call or change, matching, reflection, signals, guidance, or LLM
- No production deployment, TestFlight/App Store publication, public registration,
  friends-and-family access, analytics, notifications, or private offline cache
- No gateway, Redis, event bus, microservices, or speculative future tables

## 7. File and integration boundaries

| Boundary | Owner | Allowed changes |
|---|---|---|
| Integration and shared root | Codex | Packet, status/evidence, root workspace entries, lockfile, narrow CI registration |
| Mobile proof | Mobile workstream | `apps/mobile/` and its tests/platform files only |
| Supabase proof | Data/security workstream | `supabase/` and its tests/functions only |
| Existing receipt product | Nobody | `apps/web/`, `apps/api/`, `src/financial_os/`, `tests/`, `alembic/`, `contracts/`, and `infra/` remain unchanged |

Frozen receipt contracts and migrations may not be changed. One integration owner
applies root workspace, lockfile, CI, and Supabase migration changes.

## 8. Acceptance evidence

| Requirement | Verification | Required artifact |
|---|---|---|
| PM-0A web build | Frozen Angular production build and Capacitor configuration | Command summary, lockfile, dependency inventory, and versions |
| Owner authorization | Dedicated synthetic Firebase subject reads one synthetic row | Automated result with opaque subjects |
| Negative authorization | Missing/invalid/wrong-project/Supabase-native/non-owner/inactive/stale-version/revoked cases read/change nothing through Data API and Hosted Link function | Test matrix |
| Token lifecycle | Refresh works; inactive/version change immediately denies the prior token; provider revocation is recorded | Integration report |
| Schema/function grants | Client roles cannot use private schemas, Vault plaintext, admin tables/functions, or a service-role path before owner authorization | Grant snapshot and negative tests |
| Hosted Link session | Sandbox session is subject-bound/single-use; callback is not authority; server reports completion through `/link/token/get`; no exchange occurs | Browser/session integration report |
| PM-0B native return | Current iOS build returns on a real iPhone; Android build returns on an emulator without callback leakage | Toolchain record and device checklist |
| Failure paths | Cancel, interruption, expiry, forged/cross-subject, stale, duplicate, replay, and resume are explicit and safe | Automated/unit evidence plus device notes |
| Secret boundary | No Plaid secret/token, Firebase Admin credential, service-role key, owner UID, real project ID, Link URL, or callback material appears in source, bundle, logs, caches, screenshots, or evidence | Secret/private-data scan |
| Receipt isolation | Receipt code, contracts, migrations, infrastructure, authorization, and production behavior are unchanged | Path diff and existing CI result |

Completion requires every row to pass or an explicit owner-approved exception.

## 9. External permissions required

1. Create or select one isolated development Supabase project.
2. Register the existing Firebase project as third-party auth through private
   configuration.
3. Create/select one synthetic Firebase test subject and change only that
   subject's custom claims using read-modify-write and rollback.
4. Supply Plaid Sandbox client credentials through Edge Function project secrets.
5. Download/install pinned dependencies from official registries.
6. Use a real iPhone and Android emulator for PM-0B return-flow evidence.
7. Provide a compatible Xcode 26 build/signing lane. The current Intel macOS 13
   host with Xcode 15.2 cannot satisfy PM-0B.

Before project creation, privately record its owner, owner-selected supported U.S.
region, synthetic-only purpose, no-upgrade/billing ceiling, cost-alert owner, and
keep-or-delete decision. No real resource identifier enters repository evidence.

These permissions do not authorize production resources, Trial/live Plaid, real
bank data, store publication, or destructive cloud operations.

## 10. Supply-chain and CI rules

- Commit and enforce the pnpm lockfile; installs use the frozen lockfile.
- Pin supported Angular, Capacitor, Supabase, and test-tool majors.
- Pull-request CI is credential-free.
- External integration checks run only in the privately approved environment.
- GitHub workflow permissions are minimal; artifacts/caches contain synthetic
  output only and use bounded retention.
- Run lint, type, unit, RLS/function integration, dependency, license, secret,
  private-data, and built-bundle checks.

## 11. Timebox and fallback

- Scaffold/dependency baseline: 90 minutes.
- Firebase/Supabase authorization hypothesis: four hours or two materially
  different failed approaches, whichever comes first.
- Hosted Link server/browser hypothesis: four hours or two materially different
  failed approaches, whichever comes first.
- PM-0B starts only after its modern native lane exists.

At a limit, stop with evidence and present one bounded fallback. Do not enter an
open-ended troubleshooting loop or silently switch identity/Link models.

## 12. Stop and escalate conditions

Stop if canonical artifacts conflict; the common owner predicate cannot protect
both Data API and Edge Functions; claim mutation could weaken the receipt product;
Hosted Link requires a WebView or treats callback as authority; a secret/private
value reaches client/source/logs/evidence; a real resource or real data is needed
without authority; the receipt track must change; or evidence cannot be produced.

## 13. Handback

Return the outcome, exact files/external state changed, verification results,
acceptance table, device evidence, known limitations, residual risk, and next
smallest slice. Generated code alone is not completion.

## 14. Approval

**Architecture direction approved by:** Yemane, August 15, 2026
**Security addendum approved by:** Yemane, August 15, 2026
**PM-0A implementation authorized by:** Yemane, August 15, 2026
**External Sandbox permissions:** Authorized for the bounded synthetic/free/no-upgrade PM-0A actions in this packet
**PM-0B toolchain/device authority:** Deferred; not authorized by this approval
**Conditions:** No live financial data; no receipt-product changes
