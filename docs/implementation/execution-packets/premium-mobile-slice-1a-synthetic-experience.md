# Execution Packet — Premium Mobile PM-1A Synthetic Experience

**Status:** Owner-authorized and implemented under timebox
**Owner:** Yemane
**Integration lead:** Codex
**Date:** August 16, 2026
**Working branch:** `codex/premium-mobile-bootstrap`
**GitHub issue:** #20

## Outcome

The owner can open a real premium-mobile product surface, move between Home,
Activity, and Reflect, and complete a low-friction synthetic purchase-reflection
session. This is a product-experience slice, not another architecture proof.

## Authority and gate disposition

The approved roadmap normally gates PM-1 on complete PM-0 evidence. On August 16,
2026, after reviewing the exact PM-0 state, the owner explicitly directed Codex
to stop the native debugging loop and deliver visible product results under a
45-minute timebox. This authorizes a synthetic-only PM-1A experience in parallel
with blocked PM-0B. It does not waive PM-0B, authorize real data, or mark PM-1
complete.

## Scope

- Replace the PM-0 proof page with a premium mobile shell.
- Add Home, Activity, and Reflect navigation.
- Show an explicitly synthetic financial pulse and recent activity.
- Add search and category filters for synthetic activity.
- Add three reflection cards with touch swipe support and accessible labeled
  button alternatives.
- Preserve skip as missing evidence and support immediate undo.
- Preserve the native callback coordinator and privacy-safe test diagnostics.
- Update the GitHub Project and publish passing verification evidence.

## Non-goals

- No real financial data or owner transaction values
- No Plaid Item or access-token exchange
- No transaction synchronization or persistent label storage
- No receipt API call or receipt-product change
- No predictive guidance or AI behavior
- No production deployment, TestFlight, or PM-0 completion claim

## Acceptance evidence

1. Home, Activity, and Reflect render at a 390 × 844 phone viewport.
2. Bottom navigation changes surfaces without reload.
3. Activity search/filtering changes the visible deterministic fixture set.
4. Reflection accepts touch swipes and labeled non-swipe choices.
5. Skip creates no label; save and undo update the session immediately.
6. Lint, type checking, 19 unit tests, and production build pass.
7. Bundle and repository private-data scans pass.
8. Existing receipt code and services are not modified by this slice.

## Stop conditions

Stop at 45 minutes, on any private-data boundary failure, or if the slice requires
real provider data, a receipt-service change, or weakening the PM-0 controls.
