# Sprint 2A human review — verification evidence

**Status:** Implemented and deployed; owner-controlled correction acceptance pending
**Date:** August 14, 2026
**Scope:** Owner-only receipt correction and immutable human verification
**Data policy:** Synthetic fixtures only; private deployment identifiers intentionally omitted

## Observable outcome

An owner can open an extracted receipt in `needs_review` or `system_validated`,
correct merchant, purchase date/time, totals, and ordered line items, and submit a
complete replacement snapshot. A successful write creates one immutable child
revision with `source_type: human`, retains the extractor revision and evidence,
advances the receipt to the new current revision, records an append-only state
event, and returns `verification_status: human_verified`.

## Frozen implementation decisions

- The additive route is
  `POST /api/v1/receipts/{receipt_id}/human-revisions`.
- No database migration or backfill is required. Existing revision, line-item,
  validation-finding, and state-event tables support the complete outcome.
- The client sends the expected current parent revision. The server locks the
  receipt and returns `409 STALE_PARENT_REVISION` for a stale write.
- The client sends a complete corrected snapshot. The server validates bounds,
  exact decimals, money arithmetic, ownership, currency continuity, and legal
  state before writing anything.
- The server assigns contiguous line ordinals. The UI supports add, remove, and
  reorder, including line discounts.
- Currency correction is outside Sprint 2A. The correction must use the current
  parent revision's currency.
- Original evidence, provider output, extraction run, extractor revision, and
  prior findings are never mutated.

## AI-driven development method

Codex held product scope, contract, integration, and release authority. Claude
Code through Vertex AI acted as implementation supervisor and used exactly three
independent standard Sonnet workstreams:

1. backend and data integrity;
2. frontend and mobile product behavior;
3. security and verification.

The supervisor integrated their work. Codex then performed one bounded
cross-layer audit. The first audit proved and corrected exact-money parsing,
decimal bounds, line ordering/discount support, mobile layout, and local-time
handling. The final audit corrected canonical state-machine enforcement,
whitespace-only descriptions, NUMERIC(18,6) bounds, currency continuity,
safe-integer conversion, invalid local datetime handling, empty line-item
rejection, OpenAPI constraints, and currency exponent handling. No recursive
review loop was used.

## Local verification

| Gate | Evidence | Result |
|---|---|---|
| Python lint | `ruff check .` | Pass |
| Python formatting | `ruff format --check .` | Pass — 133 files |
| Python typing | `mypy src apps/api alembic` | Pass — 50 source files |
| Backend unit, contract, and local security | `pytest tests/unit tests/contract tests/security` without deployed credentials | Pass — 155; expected environment-dependent skips — 33 |
| PostgreSQL integration and authorization | Full integration suite plus human-revision authorization against isolated PostgreSQL 15 | Pass — 32 |
| Migration lifecycle | Alembic upgrade, one-revision downgrade, and re-upgrade against isolated PostgreSQL 15 | Pass |
| Frontend lint | ESLint | Pass |
| Frontend typing | TypeScript strict check | Pass |
| Frontend tests | Vitest | Pass — 118 tests in 11 files |
| Frontend production build | Vite PWA build | Pass |
| API definition | OpenAPI validator | Pass |
| Repository hygiene | `git diff --check` and private-data pattern scan | Pass |
| Changed security fixture | Targeted `detect-secrets` scan after removing a hard-coded synthetic JWT shape | Pass — no findings |

The database test container was temporary and removed after the migration and
test lifecycle completed.

## Acceptance disposition before publication

| Requirement | Status | Evidence or remaining gate |
|---|---|---|
| Review discovery and complete correction | Pass locally | Component tests cover form discovery, field editing, add/remove/reorder, and submit behavior |
| Immutability and lineage | Pass locally | PostgreSQL assertions retain the extractor parent and create one human child |
| Arithmetic and schema safety | Pass locally | Decimal, money, bounds, currency, and rollback tests |
| Conflict protection | Pass locally | Stale and concurrent-parent integration tests |
| Authorization | Pass locally | Missing, invalid, non-allowlisted, and cross-owner negative tests |
| Human verification state | Pass locally | Integration and UI assertions |
| Capture/extraction regression | Pass locally | Existing backend and PWA suites remain green |
| CI dependency/static security gates | Pass | [CI run 31860806179](https://github.com/YemaneSG/financial-os/actions/runs/31860806179) |
| Production deploy and privacy-safe smoke | Pass | [Deploy run 31860806300](https://github.com/YemaneSG/financial-os/actions/runs/31860806300) |
| Owner-controlled production correction | Pending | Physical-device acceptance after deployment |

## Bounded troubleshooting record

- An initial local database migration command lacked the CI database-role
  variables. It failed safely before schema changes, was rerun with the exact CI
  environment, and the complete upgrade/downgrade/upgrade lifecycle passed.
- A broad optional `detect-secrets --all-files` scan began traversing dependency
  artifacts. It was stopped as a non-blocking, incorrectly scoped check. The
  repository's private-data check passed, a targeted changed-file scan passed,
  and GitHub Gitleaks remains the authoritative full-history release gate.

No blocker exceeded two attempts or the approved troubleshooting budget.

## Publication record

- Release commit: `b03863c0ac1e845779c3e69404b85b3ebcc26139`
- GitHub CI: pass — all lint, type, test, contract, migration, dependency,
  container, infrastructure, secret, and private-data jobs completed successfully
  in [run 31860806179](https://github.com/YemaneSG/financial-os/actions/runs/31860806179).
- Production deployment: pass — immutable image build, one-shot migration,
  no-traffic API and worker candidates, candidate readiness smoke, and explicit
  traffic switches completed successfully in
  [run 31860806300](https://github.com/YemaneSG/financial-os/actions/runs/31860806300).
- PWA deployment: pass — production build, Firebase Hosting publication, and
  deployed security-header validation completed in the same deployment run.
- Owner acceptance: pending one owner-controlled correction on phone or laptop.

The docs-only closeout commit containing this final publication record has no
runtime effect and intentionally does not redeploy the already verified release
artifact.
