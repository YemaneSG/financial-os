# Claude Code Handoff — Premium Receipt Capture Dashboard

**Date:** August 16, 2026
**Owner:** Yemane
**Operating lead:** Codex
**Repository:** `YemaneSG/financial-os`
**Release branch:** `codex/production-receipt-dashboard`
**Pull request:** `#21` — Add premium receipt capture dashboard

## 1. Read first

Before planning or changing code, read in this order:

1. `AGENTS.md`
2. `docs/security/control-baseline.md`
3. `docs/product/PRD.md`
4. `docs/product/roadmap.md`
5. `docs/product/open-items-and-decisions.md`
6. `docs/implementation/execution-packets/sprint-2c-premium-capture-dashboard.md`
7. `docs/architecture/system-architecture.md`
8. `docs/architecture/data-architecture.md`
9. `docs/architecture/implementation-contracts.md`

The execution packet is the bounded implementation authority. Stop and report
any conflict with a higher-tier canonical document.

## 2. Owner-approved outcome

The existing production React receipt PWA keeps its proven capture, direct
private upload, durable acknowledgement, extraction, review, history, and
correction behavior while receiving:

- a premium light/sage mobile presentation;
- a camera-first receipt capture home;
- an owner-scoped dashboard for captured, processing, needs-review, failed, and
  recent receipts;
- honest loading, empty, error, and refresh behavior;
- a dashboard failure boundary that leaves receipt capture available.

The owner reviewed the exact React surface locally with synthetic data and
approved it for guarded production release on August 16, 2026.

## 3. Approved copy and naming boundary

- Surface label: `Dollar Trail`
- Kicker: `Every purchase leaves a clue`
- Heading: `Follow the story behind every dollar.`
- Support: `Snap the receipt now. Build a financial memory you can search,
  review, and learn from.`

`Dollar Trail` is the approved receipt-capture surface label. Do not expand this
handoff into the deferred full DollarTrace repository, package, Python namespace,
or cloud-resource rename in `DT-OPEN-001`.

## 4. Implementation inventory

- `apps/web/src/receipts/CaptureHome.tsx` — approved premium capture home and
  primary navigation.
- `apps/web/src/receipts/ReceiptDashboard.tsx` — existing-API dashboard adapter.
- `apps/web/src/styles/global.css` — premium responsive visual system.
- `apps/web/src/__tests__/CaptureHome.test.tsx` — capture behavior and hierarchy.
- `apps/web/src/__tests__/ReceiptDashboard.test.tsx` — loading, metrics, recent,
  empty, error, refresh, and bounded-query coverage.
- `docs/implementation/execution-packets/sprint-2c-premium-capture-dashboard.md`
  — scope and acceptance authority.

No backend, contract, database, migration, storage, extraction, authentication,
or infrastructure implementation changed. No production receipt record is to be
rewritten or migrated for this release.

## 5. Evidence already obtained

- Frontend type check: pass.
- Frontend lint: pass.
- Web unit/component tests: 168 passed in 15 files.
- Production PWA and service-worker build: pass.
- Private-data scan: pass.
- Phone-size visual review with synthetic data: pass.
- Owner local acceptance: pass.

The local visual-review harness was temporary, synthetic-only, and removed before
publication. Do not commit screenshots or real receipt content.

## 6. Release and production state

GitHub PR `#21` is the canonical release record. Confirm its current state and
linked workflow runs before acting; do not infer deployment from this handoff.

The owner explicitly authorized production release through the existing guarded
pipeline. Required order remains:

1. CI gate passes.
2. PR is ready and merged into `main`.
3. The existing `Deploy` workflow completes migration safety checks, candidate
   readiness, API/worker traffic handling, Firebase Hosting publication, smoke
   checks, and deployed security-header validation.
4. Confirm the phone-facing PWA receives the release.

Do not bypass a failed check or deploy directly from a laptop. Do not run a
separate production deployment once the merge-triggered workflow has succeeded.

## 7. Cost guardrail

The owner's included GitHub Actions minutes were exhausted during earlier Linux
and macOS work. The owner added a payment method and approved an Actions-only
monthly budget of **$5**, with **hard stop enabled** and threshold alerts enabled.
Avoid macOS runners unless real iOS evidence is explicitly required; this release
needs the existing Linux CI/deploy path only.

## 8. Workspace caution

The original local workspace may still contain a separate premium-mobile branch
and owner/unrelated work. Do not reset, clean, overwrite, or stage unrelated
changes. Start by inspecting `git status`, fetching `main`, and choosing an
isolated worktree when scopes overlap.

## 9. Continuation boundary

After confirming the production release and phone acceptance, stop and ask the
owner for the next bounded outcome. Do not infer authority for Plaid, Supabase,
manual transactions, transaction matching, Angular/Capacitor integration, or
receipt-service replacement from this handoff.

Receipt images remain in private Cloud Storage; structured records and statuses
remain in Cloud SQL PostgreSQL; the dashboard reads them through the existing
owner-authenticated API.
