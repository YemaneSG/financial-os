# Premium Mobile — Current Status

**Snapshot:** August 15, 2026
**Owner:** Yemane
**Operating lead:** Codex
**Phase:** PM-0A implementation
**Working branch:** `codex/premium-mobile-bootstrap`
**Implementation base:** `origin/main` at `94ba2c4`
**Operating receipt collector:** Unchanged and continuing independently

## Current outcome

Implement the smallest technical proof: Firebase owner authorization through
Supabase plus Plaid Sandbox Hosted Link server/browser completion in an isolated
Angular/Capacitor shell.

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

## In progress

- Hosted Firebase/Supabase signature, Data API, and Edge Function authorization matrix
- Selection/provisioning of the private PM-0A Supabase/Firebase/Plaid Sandbox resources
- Plaid Sandbox Hosted Link subject/session proof

## Blockers and permissions

| Item | Needed for | Status |
|---|---|---|
| GitHub Project authorization | Maintain private board and issues | Complete |
| Architecture/security/packet approval | Begin Slice 0 implementation | Complete |
| Isolated development Supabase project authority | Hosted auth/RLS proof | Authorized; credentials/session still required |
| Private Firebase configuration and minimum custom-claim authority | Third-party auth proof | Authorized; credentials/session still required |
| Plaid developer Sandbox credentials | Hosted Link proof | Not present in current environment |
| Official dependency registry access | Angular/Capacitor/Supabase scaffold | Authorized |
| Modern Xcode 26 host/runner and real iPhone | PM-0B native build/return evidence | Current host cannot satisfy; does not block PM-0A |
| Android SDK/emulator or hosted runner | PM-0B Android build/return evidence | Not installed; does not block PM-0A |
| Claude Google reauthentication | Preferred implementation lead/independent Claude review | Blocked by provider reauthentication; alternative Codex agents remain available |

No live Plaid, production Supabase, real bank connection, native toolchain, or
receipt-system change is required to start PM-0A.

## Next three actions

1. Record the PM-0A development resource choices privately and establish private sessions.
2. Run the hosted Firebase/Supabase authorization matrix and roll back synthetic claims.
3. Implement and prove the bounded Plaid Hosted Link server/browser session.

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
premium-mobile track, `5b2d8c1` is the first credential-free shell baseline.
Slice 0 will establish its first complete known-good tag only after every PM-0A
and PM-0B acceptance row passes.
