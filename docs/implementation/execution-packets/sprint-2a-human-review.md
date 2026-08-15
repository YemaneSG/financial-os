# Execution Packet — Sprint 2A Human Review and Trusted Correction

**Status:** Complete — implemented, deployed, and owner accepted
**Packet owner:** Yemane
**Operating lead:** Codex
**Implementation lead:** Claude Code through Vertex AI
**Date:** August 14, 2026
**Repository revision:** `6cb8889`

## 1. Outcome

When this work is complete, the owner can:

> Open a receipt that needs review, correct its merchant, purchase date, totals, and line items on a phone or laptop, submit the correction once, and see a durable `human_verified` revision without overwriting the original extraction or evidence.

## 2. Why now

Production capture and itemized extraction are working for real H-E-B and Costco receipts. The first observed trust gap is that a `needs_review` result can be seen but cannot be corrected. This is the smallest valuable Sprint 2 slice because it turns uncertain acquisition into analysis-ready data while daily capture continues.

## 3. Canonical inputs

Read these artifacts before planning or modifying code:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/product/PRD.md`
- `docs/product/roadmap.md`
- `docs/product/open-items-and-decisions.md`
- `docs/architecture/data-architecture.md`
- `docs/architecture/implementation-contracts.md`
- `docs/security/control-baseline.md`
- `docs/governance/ai-development-operating-model.md`
- `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md`

This packet and the listed canonical artifacts are authoritative. Conversation history is supporting context only. Tier precedence remains defined by `docs/architecture/implementation-contracts.md`.

## 4. Accepted decisions

- This is **Sprint 2A**, not all of Sprint 2. It contains only the minimal human-review vertical slice.
- A correction creates an immutable `human` receipt revision whose parent is the current revision. It never edits the extractor revision, extraction run, original model response, validation findings, or evidence assets.
- The client submits a complete corrected snapshot and the expected current revision ID. The server atomically rejects a stale write with `409 Conflict`.
- The server, not the client, re-numbers submitted line items contiguously and performs schema, money, and deterministic arithmetic validation.
- A successful correction atomically advances `current_revision_id`, sets verification to `human_verified`, and appends an auditable verification state event.
- Owner authentication and data isolation remain unchanged and mandatory.
- The existing `needs_review` receipts view becomes the review queue; a separate queue service or new navigation system is unnecessary for this slice.
- Frozen Wave 1 behavior remains backward compatible. The additive review contract is explicitly approved by the product owner through this packet.
- The user-approved troubleshooting budget is binding: spend at most 15 minutes on a non-blocker before documenting and deferring it; spend at most 30 minutes or two materially different attempts on a blocker before stopping for the owner.

## 5. Scope

- Add an owner-only additive API operation for creating one human correction from the current revision.
- Add request/response schemas and the matching OpenAPI definition.
- Persist immutable human receipt and line-item revisions using the existing tables; add a migration only if implementation proves a schema change is required.
- Enforce receipt ownership, valid parent/current revision, legal receipt state, input bounds, exact decimal handling, and atomic conflict protection.
- Re-run deterministic validation against the corrected snapshot and retain findings on the human revision.
- Add a mobile-first edit/review flow from receipt detail with safe cancel, explicit save, submission progress, conflict handling, and clear validation errors.
- Show `Human verified` after success and retain the original extraction/provenance in storage.
- Add focused backend, frontend, integration/contract, authorization, concurrency, and regression tests.
- Update canonical documentation and verification evidence.
- Push, run CI, deploy through the existing production workflow, and perform a privacy-safe production smoke test.

## 6. Non-goals and stop boundary

- Duplicate-receipt detection
- Image-quality warnings
- Expanded background/offline upload behavior
- Bank, Capital One, Ally, Plaid, statement, Amazon, email, Costco-history, or payroll ingestion
- Receipt-to-transaction matching or reconciliation
- Analytics, categorization authority, behavior reports, or financial copilot
- DollarTrace repository/code/infrastructure rename
- Rental-property itemization
- Multi-user review, approvals, comments, or collaborative workflows
- Model retraining or automatic use of corrections as training data

Do not implement these items. Record a useful discovery as a follow-up; do not expand this sprint.

## 7. Additive contract freeze

The implementation lead may make the smallest naming adjustment during contract review, but must record it before parallel implementation. The intended public shape is:

```text
POST /api/v1/receipts/{receipt_id}/human-revisions
```

Request requirements:

- `expected_parent_revision_id` is required and must equal the receipt's current revision.
- Receipt fields are a complete corrected snapshot: merchant, purchase date/time, currency, subtotal, tax, tip, discount, and total.
- Line items are a complete ordered replacement snapshot with description, optional normalized description, quantity, unit, exact decimal unit price, line total in minor units, discount in minor units, and optional category suggestion.
- Currency totals are integer minor units. Quantity and unit price cross the API as decimal strings, never binary floats.
- Text and collection sizes are bounded. Currency is a validated three-letter uppercase code.
- The endpoint is valid only for an extracted receipt with a current revision.

Success requirements:

- Return the updated receipt detail with `source_type: human` and `verification_status: human_verified`.
- A replay using the old expected parent returns `409`; it never creates a duplicate revision.
- Validation rejection creates no revision and changes no receipt state.
- Owner mismatch remains indistinguishable from a missing receipt according to the existing authorization policy.

## 8. Constraints and invariants

- Preserve `REL-001`: acknowledged evidence is never lost.
- Original images, extraction runs, raw provider output, extractor revisions, and their findings are immutable.
- No silent repair or automatic promotion of model output.
- All database changes for one correction occur in one transaction.
- Money totals use integer minor units; quantity and unit-price calculations are decimal-safe.
- Human revision lineage is explicit and acyclic through `parent_revision_id`.
- A receipt has exactly one current revision after a successful correction.
- Validation findings belong to the revision they evaluated.
- No receipt contents, signed URLs, owner identifiers, tokens, or private cloud identifiers enter logs, source control, CI output, agent handbacks, screenshots, or synthetic fixtures.
- Existing capture, HEIC/HEIF handling, upload, extraction, image retrieval, authentication, and CI behavior must not regress.

## 9. Acceptance evidence

| Requirement | Verification method | Required evidence |
|---|---|---|
| Review discovery | Component/browser test and production smoke | A `needs_review` receipt visibly offers correction; a validated receipt remains viewable |
| Complete correction | API integration test plus UI test | Merchant, date, totals, and add/edit/remove/reorder line-item behavior persists |
| Immutability and lineage | Database integration assertions | Extractor revision remains unchanged; one new `human` child becomes current |
| Arithmetic/schema safety | Unit and API negative tests | Invalid decimals, bounds, currency, and inconsistent totals return safe errors without writes |
| Conflict protection | Concurrent/stale-parent integration test | First valid write succeeds; stale second write returns `409`; one child is current |
| Authorization | Security tests | Missing, invalid, non-owner, and cross-receipt access cannot read or write corrections |
| Human verification | Integration and UI assertions | Successful correction yields `human_verified` and an append-only state event |
| Regression safety | Existing complete test suites and build | Capture, upload, extraction, retrieval, HEIC handling, CI, and security checks remain green |
| Production behavior | Privacy-safe smoke and owner acceptance | Deployed app loads; one owner-controlled correction can be completed and retrieved |

Completion requires every row to pass or an explicit owner-approved exception. A deferred non-blocker does not become an exception to data integrity, authorization, or durability.

## 10. Data and security considerations

**Data classes involved:** private financial evidence and structured data; restricted identity/configuration; public source and synthetic fixtures.

**Trust boundaries changed:** the existing owner client-to-API boundary gains one write operation. No new provider or runtime trust boundary is introduced.

**Secrets or credentials involved:** existing Firebase authentication and managed GCP deployment identities only; no new secret class.

**Required controls:** owner allowlist, server-side ownership lookup, bounded payloads, Pydantic validation, parameterized ORM access, atomic transaction, audit event, safe error envelope, privacy-safe logs, existing CSP and deployment controls.

## 11. Operational considerations

**Deployment impact:** additive web/API release. Use the existing migration-before-service deployment sequence if a migration is necessary.

**Observability:** record privacy-safe outcome codes for human-review success, validation rejection, conflict, and failure. Do not log corrected values or receipt IDs when existing logging policy treats them as private.

**Fallback:** capture and extraction continue unchanged. If review deployment fails, roll back application revisions; existing receipts and revisions remain valid and readable.

**Rollback:** redeploy the last known-good Firebase Hosting and Cloud Run revisions. Do not delete human revisions created before rollback. Any additive schema remains in place unless a separately verified downgrade is safe and necessary.

**Migration or backfill:** no backfill. Existing `needs_review` records become reviewable through their existing current extractor revision.

## 12. Parallel work plan

| Workstream | Owner/agent | Files or boundary owned | Deliverable |
|---|---|---|---|
| Integration and contract | Claude Code supervisor | Shared contract, schemas, migration decision, dependency/root configuration, integration | Frozen additive contract and coherent release |
| Backend and data | Sonnet agent A | `src/financial_os/`, `apps/api/`, backend tests; migration proposal only | Atomic human-revision service and tests |
| Frontend and product | Sonnet agent B | `apps/web/` and web tests | Mobile-first correction workflow and tests |
| Security and verification | Sonnet agent C | Security/contract/E2E tests and evidence; CI changes only if required | Independent risk review and release evidence |

The three workstreams perform independent analysis within their boundaries. They do not inherit conclusions from one another. Only the supervisor edits frozen shared contracts, migrations, and root configuration or accepts a proposed delta.

## 13. Execution and review protocol

1. Supervisor reads canonical inputs and inspects the working production implementation.
2. Supervisor records the final route/schema naming and whether a migration is required.
3. Three standard Sonnet agents implement the bounded workstreams; agent teams are not used.
4. Supervisor integrates and runs one independent review pass from product, engineering, and security/operations perspectives.
5. Findings are proved with code, tests, or primary documentation before adoption. Each is fixed, deferred as a non-blocker, or escalated as a blocker.
6. There are no recursive review loops. After one fix-and-retest pass, unresolved issues follow the troubleshooting budget.
7. Only a fully green release is pushed/deployed. Production deployment uses the existing workflows and rollback path.

## 14. Required checks

- [x] Backend formatting, lint, type checking, unit, integration, contract, and security tests
- [x] Frontend formatting, lint, type checking, unit/component tests, and production build
- [x] Stale-write and transactional rollback tests
- [x] Owner-only negative authorization tests
- [x] Existing synthetic capture regression suites
- [x] OpenAPI/schema compatibility validation
- [x] Migration upgrade/downgrade validation; no Sprint 2A migration required
- [x] Local secret and private-data scans; authoritative CI Gitleaks gate pending publication
- [x] Dependency/static security checks already enforced by CI
- [x] One bounded three-perspective independent review and finding disposition
- [x] Production deploy and privacy-safe smoke evidence
- [x] Owner-controlled production correction acceptance
- [x] Canonical roadmap, decision register, packet, and evidence updated

## 15. Troubleshooting budget and stop rules

### Non-blocker

- Timebox diagnosis to 15 minutes.
- If the sprint outcome and release gates remain achievable, document the symptom, evidence, impact, and next action; mark it deferred and continue.
- A cosmetic issue, optional enhancement, or unavailable nonessential check is not allowed to start a debugging loop.

### Blocker

- Timebox diagnosis to 30 minutes or two materially different attempts, whichever occurs first.
- Stop all deployment/push work and wait for the owner if the blocker prevents a safe correction flow, required integrity/auth/security evidence, a green required check, or rollback confidence.
- Report the exact failing gate, evidence, attempts made, and safest next choices. Do not keep retrying variations of the same approach.

### Immediate stop

Stop immediately for a destructive migration or infrastructure plan, discovered secret/private-data exposure, loss or overwrite of acknowledged evidence, unsafe authorization behavior, a required scope expansion, or missing authority for an external side effect.

## 16. Handback contract

The implementation lead returns:

1. Observable product outcome
2. Exact files, contract, migration, and behavior changed
3. Verification commands and results
4. Acceptance evidence with pass, fail, deferred, or owner-approved exception
5. Review findings and disposition
6. Commit, CI/deploy run, and deployed revision evidence
7. Known limitations and residual risks
8. Updated decisions and next smallest slice

## 17. Approval

**Approved by:** Yemane
**Date:** August 14, 2026
**Conditions:** Avoid infinite debugging; timebox and defer non-blockers, stop for the owner on timeboxed blockers, and document decisions and development method as canonical project artifacts.

---

## 18. Contract freeze record (recorded August 14, 2026)

**Route:** `POST /api/v1/receipts/{receipt_id}/human-revisions`
**Status:** Frozen. No further naming or schema changes permitted without supervisor approval and a new packet.

The public contract matches the shape defined in section 7 with the following confirmed implementation details:

- `expected_parent_revision_id` (UUID, required) — must equal the receipt's current revision ID.
- `currency` (string, required) — three-letter uppercase ISO 4217 code; read from the parent revision by the client and sent as-is.
- The server rejects a correction whose currency differs from the current parent revision; currency correction is outside Sprint 2A.
- `total_minor` (integer, required, non-negative, ≤ BIGINT_MAX = 9,223,372,036,854,775,807).
- All other money fields (`subtotal_minor`, `tax_minor`, `tip_minor`, `discount_minor`) optional, same bounds.
- `purchase_timezone` is the client-submitted IANA timezone string (auto-detected from device; not manually entered).
- Line item `quantity` and `unit_price_decimal` cross the wire as decimal strings, validated as non-negative finite NUMERIC(18,6) values.
- Server re-numbers line items 1..N; client ordinals are ignored.
- Response is the full `ReceiptDetailSchema` with `source_type: "human"` and `verification_status: "human_verified"`.

## 19. Migration decision (recorded August 14, 2026)

**Decision:** No Alembic migration required for Sprint 2A.

The existing schema (`receipt_revisions`, `line_item_revisions`, `validation_findings`, `state_events`) is sufficient to persist human revisions. The `source_type` column on `receipt_revisions` already accepts the string `"human"`. The `verification_status` column already includes `"human_verified"`. The `state_events` table records the verification transition. No schema change is necessary.
