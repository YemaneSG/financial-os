# Premium Mobile — Current Status

**Snapshot:** August 16, 2026
**Owner:** Yemane
**Operating lead:** Codex
**Phase:** PM-0A complete; PM-0B blocked; PM-1A synthetic experience implemented
**Working branch:** `codex/premium-mobile-bootstrap`
**Implementation base:** `origin/main` at `94ba2c4`
**Operating receipt collector:** Unchanged and continuing independently

## Current outcome

PM-0A is complete. PM-0B builds on current iOS and Android toolchains, but its
latest Android emulator run received the callback and rejected it under the local
return policy; real HTTPS association and real-iPhone evidence also remain open.
The owner stopped the debugging loop and authorized PM-1A in parallel. The app now
has a real synthetic Home, Activity, and Reflect product experience.

## Completed

- Controlled research Tracks 1–8 and consolidation
- Shared-conversation idea recovery and focused competitor/HCI correction
- Premium-mobile PRD
- Opus architecture proposal normalized against current vendor documentation
- Codex architecture gate review
- Separate product-track and GitHub delivery decisions recorded
- Premium-mobile roadmap, canonical architecture candidate, threat model,
  security addendum, and revised Slice 0 packet prepared
- Dedicated premium-mobile branch created from `origin/main`
- [Private GitHub Project](https://github.com/users/YemaneSG/projects/2) created
  and linked; PM-0 issues #13–#18 seeded
- Initial Gate A reviews completed: two Approve with conditions and one Reject;
  the rejected packet conditions were corrected in revision 2
- Gate A revision-2 re-review completed: one Approve and two Approve with
  conditions; no blocking/high design finding remains
- Owner approved the architecture, security addendum, threat model, PM-0A packet,
  synthetic/free/no-upgrade Sandbox actions, and official dependency downloads
- Owner-approved Gate A snapshot committed at `afef862`, pushed, and opened as
  draft pull request #19
- Isolated Angular/Capacitor scaffold, native project preparation, frozen
  dependency graph, and credential-free mobile CI job completed locally
- Mobile scaffold committed at `5b2d8c1`; credential-free GitHub CI run #48 passed
- Local Supabase owner predicate, restrictive RLS proof, and caller-scoped Edge
  Function boundary implemented; 26 database assertions and 6 boundary tests pass
- Isolated free hosted Supabase project created in the approved Ohio region;
  Firebase third-party trust, migration, owner relationship, and Edge Function deployed
- Hosted database matrix passes all 26 assertions; anonymous function access is
  fail-closed and unsupported methods are rejected
- Firebase-signed hosted lifecycle passes: valid owner 204, stale version 403,
  refreshed version 204, inactive owner 403, disabled provider 403, restored 204
- Direct Data API/RLS returns exactly the one synthetic proof row; the temporary
  synthetic identity was deleted and its temporary sign-in provider disabled
- Plaid Hosted Link local boundary passes 23 function tests and 34 database
  assertions; database lint and Edge runtime type checks pass
- Hosted private session migration and 10-assertion smoke pass; create/status
  Edge Functions are deployed with anonymous POST denied and GET rejected
- Plaid Sandbox credentials are stored only as encrypted Edge Function secrets;
  after a private terminal diagnostic briefly rendered the initial Sandbox
  secret, it was rotated, the replacement was verified and deployed, the old
  secret was revoked, and terminal/browser credential state was cleared
- Live owner authorization and Hosted Link creation pass with 204 and 201
- Live Sandbox completion returns `succeeded` twice, explicit exit returns
  `cancelled` twice, and controlled expiry returns `expired` twice; none of the
  status responses contains a public token, link token, or access token
- Synthetic cleanup completed: three session rows and one owner row removed,
  two temporary Firebase users deleted, temporary Email/Password disabled,
  temporary Identity Toolkit API enablement reversed, and the temporary
  Firebase Authentication Admin role removed and verified absent
- Owner explicitly authorized the bounded PM-0B publication, credential-free
  current-platform builds, one owner-controlled HTTPS Universal/App Link, and
  synthetic real-iPhone/Android-emulator return tests on August 16, 2026
- Corrected the PM-0A server/native completion-scheme mismatch before device use
- Added an exact callback classifier and coordinator that discards raw URL
  material, treats the callback only as a wake-up, and never displays success
  without the server-held session result
- Added fixed custom-scheme declarations for iOS and Android and a shared iOS
  build scheme; an HTTPS Universal/App Link remains intentionally absent until
  the real host and platform associations exist
- Added path-scoped GitHub native CI for Android and macOS 26/Xcode 26 plus a
  generated-bundle credential scan
- Local PM-0B preparation passes mobile lint, type checking, 17 tests, production
  build, 25 Edge-function tests, plist/XML checks, private-data scan, bundle scan,
  and whitespace validation
- Corrected the Android runner to Java 21 and obtained green Android and macOS
  26/Xcode 26 builds in native run 31970837438; full CI run 31970837452 also
  passed its final gate
- Owner stopped the PM-0B debugging loop and authorized bounded synthetic PM-1A
  product work under a 45-minute timebox
- Replaced the visible native-proof page with a premium mobile Home, searchable
  Activity, and accessible three-card Reflect experience
- Added touch swipe, labeled non-swipe choices, skip-as-missing-evidence,
  completion, and immediate undo behavior
- Verified all three screens at a 390 × 844 viewport; mobile lint, type checking,
  19 tests, production build, credential scan, and private-data scan pass

## In progress

- PM-0B Android callback policy correction, intentionally paused after the latest
  native run received the callback but rejected it under local policy
- Owner-controlled HTTPS Universal/App Link selection and provider association
- Real-iPhone and Android-emulator Hosted Link return verification

## Blockers and permissions

| Item | Needed for | Status |
|---|---|---|
| GitHub Project authorization | Maintain private board and issues | Complete |
| Architecture/security/packet approval | Begin Slice 0 implementation | Complete |
| Isolated development Supabase project authority | Hosted auth/RLS proof | Complete; isolated free project and hosted matrix verified |
| Private Firebase configuration and minimum custom-claim authority | Third-party auth proof | Complete; synthetic users deleted, temporary provider/API disabled, temporary admin role removed |
| Plaid developer Sandbox credentials | Hosted Link proof | Complete; stored as encrypted backend secrets only |
| Official dependency registry access | Angular/Capacitor/Supabase scaffold | Authorized |
| Modern Xcode 26 host/runner and real iPhone | PM-0B native build/return evidence | GitHub macOS 26/Xcode 26 compile passed; signed real-iPhone delivery still required |
| Android SDK/emulator or hosted runner | PM-0B Android build/return evidence | GitHub Android compile and emulator boot passed; latest callback was rejected by local policy |
| Owner-controlled HTTPS Universal/App Link | Institution OAuth return and native mode | Exact host and platform association still required; no placeholder committed |
| Claude Google reauthentication | Preferred implementation lead/independent Claude review | Blocked by provider reauthentication; alternative Codex agents remain available |

No Plaid Trial/live access, real bank connection, production deployment, or
receipt-system change is authorized in PM-0.

## Next three actions

1. Review and accept the PM-1A product experience on the open local preview.
2. Configure one owner-controlled HTTPS host with Apple and Android association,
   register it with Plaid, and switch the Sandbox function to native mode.
3. Correct the bounded callback policy and run success, cancel, interruption,
   resume, and privacy checks on a real iPhone
   and Android emulator; do not call PM-0 complete before both pass.

## Active canonical artifacts

- `docs/product/premium-mobile-app-PRD.md`
- `docs/product/open-items-and-decisions.md` — DT-DEC-005/006
- `docs/security/premium-mobile-control-addendum.md`
- `docs/security/premium-mobile-threat-model.md`
- `docs/architecture/premium-mobile-system-architecture.md`
- `research/architecture_runs/2026-08-15-premium-mobile-v1/OPUS-ARCHITECTURE-PROPOSAL.md`
- `research/architecture_runs/2026-08-15-premium-mobile-v1/CODEX-ARCHITECTURE-GATE-REVIEW.md`
- `docs/implementation/execution-packets/premium-mobile-slice-0-auth-plaid-spike.md`

## Last known-good definition

For the receipt product, `origin/main` remains the production baseline. For the
premium-mobile track, `5b2d8c1` remains the first credential-free shell
baseline. PM-0A now has complete server/browser evidence; Slice 0 will establish
its complete known-good tag only after the separate PM-0B native acceptance rows
pass.
