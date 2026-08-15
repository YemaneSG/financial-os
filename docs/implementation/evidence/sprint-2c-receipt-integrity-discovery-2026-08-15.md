# Sprint 2C receipt integrity and discovery — verification evidence

**Status:** Implemented and locally verified; publication, production backfill, and owner acceptance pending
**Date:** August 15, 2026
**Scope:** Deterministic duplicate classification and owner-only receipt discovery
**Data policy:** All tracked fixtures and evidence are synthetic or privacy-safe

## Observable outcome

Receipt capture now classifies exact repeated evidence immediately after durable
upload and reruns semantic classification after extraction or human correction.
Every artifact remains preserved. Confirmed duplicates link directly to the
earliest acknowledged canonical receipt; incomplete same-day evidence is only
suspected and never auto-merged.

The mobile Receipts view searches the complete owner-scoped history by normalized
merchant or canonical item description. Quick filters and the advanced sheet
compose with date, amount, processing, verification, duplicate state, and sort.
Results keep the existing card presentation, group by effective purchase month,
explain item matches, paginate with filter-bound keyset cursors, and restore view
state after detail navigation.

## Frozen implementation decisions

- Duplicate detection is an independent state axis with `unchecked`, `unique`,
  `suspected_duplicate`, and `confirmed_duplicate` projections plus append-only
  state transitions.
- Exact image manifests and complete semantic signatures use versioned SHA-256
  fingerprints. Empty or incomplete item evidence cannot confirm a semantic
  duplicate. Fingerprints never enter public responses or logs.
- Canonical selection is deterministic and converges an observed cluster to one
  direct root. The database rejects self-links. Evidence is never deleted,
  overwritten, or merged.
- Backfill is oldest-first, resumable, aggregate-only, and rollback-only unless
  `--apply` is explicit. The operational procedure is documented in
  `docs/operations/runbooks/receipt-deduplication-backfill.md`.
- Search terms use an authenticated JSON-body request, literal wildcard escaping,
  bounded normalized input, owner-scoped parameterized SQL, and no raw OCR.
- Search cursors bind version, sort, and a digest of the request filters. Invalid
  or cross-filter reuse returns a safe validation error instead of silently
  changing page semantics.
- Receipt list, detail, and search expose duplicate status and canonical receipt
  ID only. Evidence and semantic fingerprints remain private server projections.
- The legacy receipt list now joins current revisions in one query and uses a
  timestamp-plus-UUID cursor, removing the card-level N+1 query.

## AI-driven development method

Codex retained product, contract, security, integration, and release authority.
Two independent Claude Code Sonnet workstreams implemented integrity and
discovery in isolated worktrees. Codex reviewed both outputs, corrected
idempotency, dry-run transaction behavior, canonical convergence, semantic
completeness, strict cursor semantics, stale-response handling, filter
composition, date boundaries, focus management, public schemas, OpenAPI, and the
legacy list query before integration.

No issue exceeded the approved 30-minute troubleshooting boundary. The first
Claude background mode could not edit, so the same bounded work was restarted in
the documented edit-capable mode. Localhost database access initially hit the
sandbox boundary and was rerun once with scoped authorization. Generated
integration fixtures then exposed event-loop and insert-order defects; those test
harness issues were corrected without changing product scope.

## Local verification

| Gate | Evidence | Result |
|---|---|---|
| Python lint and formatting | `ruff check .`; `ruff format --check .` | Pass — 155 files formatted |
| Python typing | `mypy src apps/api alembic` | Pass — 58 source files |
| Backend unit and contract | `pytest tests/unit tests/contract` | Pass — 243 tests |
| Migration lifecycle | Alembic upgrade, downgrade one revision, and re-upgrade on PostgreSQL 15 | Pass |
| Full PostgreSQL regression | `pytest tests/integration` on isolated PostgreSQL 15 | Pass |
| Duplicate/backfill focus | Integrity integration module | Pass — 11 tests |
| Search/pagination focus | Discovery integration module | Pass — 23 tests |
| Frontend lint and typing | ESLint zero-warning gate; strict TypeScript | Pass |
| Frontend tests | Complete Vitest suite | Pass — 162 tests in 14 files |
| Production PWA build | Vite and service-worker build | Pass |
| API definition | OpenAPI 3.1 validator | Pass |
| Security regression | Complete `tests/security` suite on isolated PostgreSQL 15 | Pass — environment-dependent cases skipped as designed |
| Private-data scan | `scripts/check-private-data.sh` | Pass |
| Repository hygiene | `git diff --check` | Pass |

The PostgreSQL container and all synthetic database contents were removed after
verification. React Router emits its existing version-7 future notices, and a
small number of mocked immediate-response cases emit test-only React `act()`
warnings. They are non-blocking and do not affect production behavior.

## Release gates remaining

- GitHub feature-branch and pull-request CI, including dependency, container,
  infrastructure, secret, private-data, and OpenAPI jobs.
- Safe production deployment: migration, no-traffic API/worker candidates,
  readiness checks, traffic switch, and PWA publication.
- Production backfill dry run, explicit apply, convergence verification, and
  privacy-safe health checks.
- Owner acceptance on iPhone/laptop using private receipts; no private values or
  evidence will be added to this record.
