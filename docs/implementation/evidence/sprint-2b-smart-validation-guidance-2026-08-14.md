# Sprint 2B smart validation guidance — verification evidence

**Status:** Implemented and locally verified; publication and owner acceptance pending
**Date:** August 14, 2026
**Scope:** Deterministic arithmetic explanations, ranked draft proposals, and explicit confirm-as-shown
**Data policy:** All tracked fixtures and evidence are synthetic or privacy-safe

## Observable outcome

An owner opening a receipt with a material arithmetic exception sees the signed
currency difference, receipt and calculated totals, the component equation, and
up to three deterministic proposals. A proposal identifies the affected field or
item ordinal, shows the matching amount and reason, and applies only to the
editable draft. The form immediately recalculates the total and focuses the
affected control before the owner saves.

The owner can instead choose `Confirm as shown`. That path requires one explicit
confirmation, verifies that every editable value semantically equals the locked
parent snapshot, creates an immutable human child, retains failed findings, and
records `human_confirmed_exception`. The UI then states
`Human confirmed — arithmetic exception`; it never represents the failed equation
as passed.

## Frozen implementation decisions

- All money arithmetic uses integer minor units. Quantity-by-price comparisons
  use exact decimals; no language model calculates or authorizes corrections.
- `review_disposition` defaults to `corrected`, preserving the Sprint 2A request
  contract. `confirmed_as_shown` is explicit and cannot carry changed values.
- Snapshot equality covers merchant, purchase instant and timezone, currency,
  every receipt money field, ordered raw and normalized line descriptions,
  quantity, unit, unit price, line total, line discount, and category suggestion.
- Receipt finding details are projected through a check-code, key, type, and
  bounded-string allowlist before the owner-only response is serialized.
- Line-item-to-subtotal validation is not applicable when any line total is
  missing; a partial item sum cannot create a false review failure or proposal.
- Candidate ranking simulates allowlisted draft patches and reruns material
  checks. A strong candidate must uniquely restore all material equations;
  equally effective candidates are labeled ambiguous. At most three are returned.
- No migration, provider, secret, public endpoint, background job, or new
  infrastructure was required.
- A unique two-line deletion hypothesis is deferred. The current contract lacks
  sufficient multi-target evidence and UX to make a double-removal proposal safe;
  one-line removal is already constrained by equation restoration.

## AI-driven development method

Codex retained product, scope, integration, security, and release authority.
Claude Code through Vertex AI acted as implementation supervisor and used exactly
three independent standard Sonnet workstreams: backend/data, frontend/product,
and security/verification. Codex then performed the permitted independent audit
and one bounded fix pass.

The audit found and corrected full-snapshot bypass coverage, exact confirm payload
construction, partial-line false positives, ambiguity labeling, stable ranking,
candidate amount/reason presentation, affected-field focus, exception-state copy,
mobile styling, and response-schema allowlisting. The Claude fix process was
stopped after its announced quiet boundary; saved work was verified and completed
locally without restarting the process or entering a troubleshooting loop.

## Local verification

| Gate | Evidence | Result |
|---|---|---|
| Python lint | `ruff check .` | Pass |
| Python formatting | `ruff format --check .` | Pass — 139 files |
| Python typing | `mypy src apps/api alembic` | Pass — 51 source files |
| Complete local backend regression | `pytest -q` without external credentials | Pass; expected environment-dependent skips only |
| PostgreSQL integration | Full `tests/integration` against disposable PostgreSQL 15 | Pass — 28 tests |
| PostgreSQL authorization/security | Full `tests/security` with database access | Pass — 43; 24 deployment/credential-specific skips |
| Migration lifecycle | Alembic upgrade, downgrade one revision, and re-upgrade | Pass |
| Frontend lint | ESLint with zero warnings | Pass |
| Frontend typing | TypeScript strict check | Pass |
| Frontend tests | Vitest | Pass — 135 tests in 13 files |
| Frontend production build | Vite PWA build | Pass |
| API definition | OpenAPI validator | Pass |
| Repository hygiene | `git diff --check` and private-data pattern scan | Pass |
| Changed-file secret scan | Targeted `detect-secrets` scan | Pass — no findings |

The PostgreSQL container was disposable and automatically removed after the
migration, integration, and security lifecycle completed.

## Bounded troubleshooting record

- The sandbox initially blocked localhost and Docker access. The commands were
  rerun once with scoped authorization.
- The first migration connection omitted CI database-role variables and stopped
  safely before schema changes. The exact CI environment was supplied once and
  the full migration lifecycle passed.
- One new security test expected malformed-path validation before authentication.
  The application correctly returned `401`; the test was corrected to authenticate
  before asserting `422`, and the complete security suite passed on the next run.
- The desktop shell did not expose Node on `PATH`; the bundled workspace Node
  runtime executed the unchanged project tools successfully. No machine setup or
  dependency change was required.

No issue exceeded two materially distinct attempts or the approved time budget.

## Publication record

Pending commit, GitHub CI, production deployment, privacy-safe smoke, and owner
acceptance. This section will be closed with immutable run references after the
release gates complete.
