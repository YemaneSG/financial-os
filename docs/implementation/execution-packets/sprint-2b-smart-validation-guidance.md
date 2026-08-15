# Execution Packet — Sprint 2B Smart Validation Guidance

**Status:** Implemented and locally verified — publication and owner acceptance pending
**Packet owner:** Yemane
**Operating lead:** Codex
**Implementation lead:** Claude Code through Vertex AI
**Date:** August 14, 2026
**Repository revision:** `95b2aab`

## 1. Outcome

When this work is complete, the owner can open a receipt with an arithmetic
exception and receive a ranked, evidence-backed explanation that identifies the
exact difference and relevant receipt field or line item. A strong proposal can
be applied to the editable draft and confirmed in one or two taps. The owner may
instead confirm the receipt exactly as evidenced without pretending its arithmetic
passed.

## 2. Product principle

Receipt review is an exception-routing decision, not a forensic accounting task.
The system performs the search, arithmetic, candidate generation, and ranking.
The owner confirms, rejects, chooses among a few candidates, or uses manual edit
as a fallback.

Target interaction time:

- strong proposal: at most 15 seconds after opening review;
- ambiguous proposal: at most 30 seconds using ranked choices or confirm as shown.

## 3. Canonical inputs

- `AGENTS.md`
- `CLAUDE.md`
- `docs/security/control-baseline.md`
- `docs/product/PRD.md`
- `docs/product/roadmap.md`
- `docs/product/open-items-and-decisions.md`, especially `DT-OPEN-002`
- `docs/architecture/data-architecture.md`
- `docs/architecture/implementation-contracts.md`
- `docs/governance/ai-development-operating-model.md`
- `docs/implementation/execution-packets/sprint-2a-human-review.md`
- `docs/implementation/evidence/sprint-2a-human-review-2026-08-14.md`

This packet and the listed canonical artifacts are authoritative. Conversation
history is supporting context only.

## 4. Accepted research and design decisions

- Receipt extraction commonly separates summary fields from line-item groups.
  Reconciliation must reason across both rather than treat a mismatch as a single
  opaque validation result.
- Suggestions use deterministic integer-minor-unit arithmetic. No language model
  calculates, applies, or authorizes a correction.
- Labels such as discount, coupon, or savings may strengthen evidence but never
  override arithmetic.
- A matching amount alone is a `Possible` candidate. A `Strong` recommendation
  must restore every affected equation and be uniquely preferred by the bounded
  ranking rules.
- Applying a proposal mutates only the client draft and immediately recomputes
  the preview. The existing server-side correction validation remains the final
  authority before persistence.
- Present at most three proposals. Do not use an open-ended subset-sum search that
  can manufacture coincidental explanations.
- Evidence bands are `strong`, `possible`, and `ambiguous`; do not invent
  probability percentages.
- `Confirm as shown` means the human confirms the evidence, not that arithmetic
  passed. Failed deterministic findings remain attached to the immutable human
  revision and the UI states `Human confirmed — arithmetic exception`.
- No database migration or new infrastructure is expected. Existing immutable
  revisions, validation findings, and privacy-safe state-event reason codes are
  sufficient.

Primary research references:

- AWS Textract receipt fields distinguish subtotal, discount, total, and line
  item price: <https://docs.aws.amazon.com/textract/latest/dg/invoices-receipts.html>
- Google Document AI expense parsing distinguishes normalized totals and line
  item amounts/descriptions: <https://docs.cloud.google.com/document-ai/docs/processors-list>
- Google PAIR recommends explanations tied to user actions and calibrated
  uncertainty: <https://pair.withgoogle.com/chapter/explainability-trust>
- NIST AI RMF requires documented knowledge limits and human oversight roles:
  <https://airc.nist.gov/airmf-resources/airmf/5-sec-core/>

## 5. Scope

- Add deterministic receipt reconciliation output for the current revision.
- Add `LINE_ITEMS_TO_SUBTOTAL_V1`, comparing subtotal with both gross and
  line-discount-adjusted item sums without assuming one retailer-wide convention.
- Return safe structured finding details and ranked correction proposals from the
  owner-only receipt-detail API.
- Add a mobile-first explanation and proposal UI that points to exact fields or
  item ordinals and auto-scrolls/focuses the relevant editable control.
- Add `Apply and preview`, `Confirm as shown`, and existing manual edit paths.
- Add an explicit review disposition to the existing human-revision operation.
- Permit failed arithmetic only for the explicit confirm-as-shown disposition and
  only when the submitted snapshot semantically equals the current parent.
- Preserve failed findings and record a privacy-safe
  `human_confirmed_exception` verification event.
- Add backend, frontend, integration, contract, authorization, accessibility,
  stale-write, immutability, and regression tests.
- Update canonical decisions and evidence, publish, deploy, and run the existing
  privacy-safe smoke gates.

## 6. Non-goals and stop boundary

- Automatically persist or silently apply any proposal
- Open-ended subset-sum, probabilistic matching, or invented confidence scores
- LLM-based correction, model retraining, or merchant-specific learned policy
- Bounding-box/image-region extraction or reprocessing existing private images
- Duplicate-receipt detection, image-quality warnings, or expanded offline retry
- Plaid, bank, statement, Amazon, email, Costco-history, payroll, or transaction
  ingestion and matching
- Analytics, categorization authority, behavior reporting, or financial copilot
- DollarTrace repository/code/infrastructure rename
- Rental-property itemization or multi-user workflows

Record useful discoveries as follow-ups; do not expand this sprint.

## 7. Additive API contract

The existing owner-only operations remain:

```text
GET  /api/v1/receipts/{receipt_id}
POST /api/v1/receipts/{receipt_id}/human-revisions
```

### Receipt detail additions

`validation_findings[]` adds the internally generated, privacy-safe `observed`
and `expected` evidence. Values are bounded scalar numbers, strings, or booleans;
no receipt text or identifiers are included.

`review_guidance` is nullable and includes:

- signed receipt-total difference and the exact component equation;
- gross and net line-item sums and subtotal differences when computable;
- at most three ranked `review_candidates`;
- candidate kind, evidence band, target receipt field or item ordinal, amount,
  privacy-safe reason codes, before/after equations, and an allowlisted draft
  patch.

Allowed draft patch operations are limited to:

- set or clear a receipt subtotal or discount;
- set or clear a line discount;
- set a line total from exact quantity-by-unit-price arithmetic;
- remove one identified line item.

The server never accepts a candidate ID as correction authority. The client
applies a proposal to its draft; the complete resulting snapshot is submitted
through the existing validated human-revision operation.

### Human revision disposition

Add `review_disposition`:

- `corrected` — default for backward compatibility; all material deterministic
  findings must pass before persistence.
- `confirmed_as_shown` — submitted snapshot must semantically equal the locked
  current parent. Failed arithmetic findings are retained and allowed. The event
  reason is `human_confirmed_exception` when any material finding fails, otherwise
  `human_confirmed_as_shown`.

For both dispositions, expected-parent conflict protection, ownership, currency,
state-machine enforcement, transaction atomicity, and immutable lineage remain
unchanged.

## 8. Candidate generation and ranking contract

Use exact integers for money and decimal-safe quantity arithmetic.

1. Compute the top-level equation and signed delta:
   `total - (subtotal + tax + tip - discount)`.
2. Compute gross line sum and net line sum after explicit line discounts.
3. Collect exact matches for the absolute discrepancy across receipt discount,
   line discounts, line totals, and per-line quantity-price differences.
4. Generate only bounded minimal-edit hypotheses:
   - clear a duplicated receipt discount;
   - use a supported gross or net item sum as subtotal;
   - clear a duplicated line discount;
   - replace a line total with exact quantity-by-price output;
   - remove one line, optionally paired with setting the supported subtotal;
   - consider one unique pair of lines only when required to explain the gap.
5. Simulate each patch and rerun every material deterministic check.
6. Rank by exact match, number of failed equations restored, keyword/adjacency
   support, uniqueness, and minimum edit count.
7. A strong candidate must produce no material arithmetic failure and must not tie
   another candidate at the same evidence level. Otherwise downgrade it.
8. Return at most three deterministic candidates with stable ordering.

If no safe proposal exists, return the arithmetic explanation and relevant amount
matches as possible evidence, plus confirm-as-shown and manual edit. Never tell the
owner to scan the receipt unaided.

## 9. UI contract

For a failed totals check, show:

- `Difference: <signed formatted amount>`;
- receipt total, calculated total, and the exact component equation;
- the top proposal with item description/ordinal or field, why it matches, and
  evidence band;
- `Apply and preview`, `Confirm as shown`, and `Edit manually` actions.

Applying a proposal updates the draft, scrolls/focuses the affected control,
recalculates the live preview, and never saves automatically.

Confirm as shown requires one explicit confirmation dialog or inline confirmation
that says the evidence will be preserved with an arithmetic exception. It must not
require retyping values or opening the image.

## 10. Acceptance evidence

| Requirement | Verification method | Required evidence |
|---|---|---|
| Exact explanation | Unit/API/component tests | Signed delta and component equation render in currency |
| Discount duplication | Backend and UI tests | Synthetic receipt-level discount match yields a strong clear-discount proposal and balanced preview |
| Exact item lookup | Candidate-engine tests | Synthetic discrepancy identifies the exact item ordinal/description and appropriate bounded action |
| Ambiguity safety | Candidate-engine/UI tests | Multiple equal matches are downgraded and presented without silent selection |
| No coincidental deletion | Negative tests | Amount-only match that does not restore equations never becomes a strong removal proposal |
| Live preview | Component tests | Applying a proposal updates draft values and all arithmetic results before save |
| Confirm as shown | PostgreSQL integration test | Identical parent snapshot creates one human child with failed finding retained and exception event |
| Bypass prevention | Security/integration tests | Changed payload cannot use confirmed-as-shown to bypass validation |
| Immutability/conflict | Integration tests | Parent/evidence unchanged; stale replay returns `409`; one current revision |
| Authorization | Security tests | Missing, invalid, non-owner, and cross-owner requests reveal or change nothing |
| Regression | Complete existing suites/build | Capture, extraction, correction, HEIC, retrieval, auth, and PWA remain green |
| Production | Existing deploy and privacy-safe smoke | Migration job, candidate readiness, traffic switch, hosting, and headers pass |

## 11. Security, data, and operational considerations

- No new trust boundary, provider, secret class, storage class, or public endpoint.
- Guidance is owner-only private financial content and must not enter logs, source,
  screenshots, analytics, or CI artifacts.
- Candidate reason codes and metrics contain no amounts, descriptions, receipt IDs,
  or owner identifiers beyond the existing approved logging policy.
- Escaped plain-text rendering remains mandatory for item descriptions.
- Candidate patches are an allowlisted UI convenience, never server-side action
  authority.
- `Confirm as shown` is explicit, auditable, stale-write protected, and cannot
  change parent values.
- Rollback redeploys the last known-good API, worker, and PWA revisions. Existing
  human-confirmed exception revisions remain immutable and readable.
- No backfill. Existing reviewable receipts receive guidance when loaded.

## 12. Workstreams

| Workstream | Owner/agent | Boundary | Deliverable |
|---|---|---|---|
| Contract/integration | Claude supervisor | Shared schema, OpenAPI, migration decision, integration | Frozen additive contract and coherent release |
| Backend/data | Sonnet agent A | Domain/service/API backend and focused tests | Exact reconciliation, proposals, confirm-as-shown persistence |
| Frontend/product | Sonnet agent B | PWA and component tests | Fast action-oriented review and live preview |
| Security/verification | Sonnet agent C | Negative, ambiguity, auth, and evidence review | Independent bypass/privacy/regression evidence |

Only the supervisor edits frozen contracts or root configuration. Agents use
synthetic fixtures and perform independent analysis within their boundary.

## 13. Required checks

- [x] Backend lint, format, typing, unit, integration, contract, and security tests — complete local regression green; PostgreSQL integration 28 passed; database security 43 passed with 24 credential/deployment-specific skips
- [x] Frontend lint, typing, unit/component/accessibility tests, and build — 135 tests in 13 files passed; TypeScript and production PWA build clean
- [x] Exact-money, candidate ranking, ambiguity, and no-coincidental-delete tests — `test_candidate_ranking.py` (16), `test_reconciliation.py` (7)
- [x] Confirm-as-shown equality, failure retention, immutability, and conflict tests — complete editable-snapshot coverage plus `test_human_revision_disposition.py` (5 PostgreSQL tests)
- [x] Owner-only negative authorization tests — new confirm-as-shown authorization cases and existing human-revision authorization suite passed against PostgreSQL
- [x] OpenAPI validation and backward-compatibility review — additive only: no existing fields removed, all new fields nullable or with defaults
- [x] Migration upgrade/downgrade validation — no migration required (confirmed); existing schema sufficient
- [ ] Secret and private-data scans — local private-data pattern scan passed; authoritative GitHub Gitleaks gate pending publication
- [x] One bounded product/engineering/security review — independent agents; findings documented below
- [ ] CI, production deployment, readiness smoke, and hosting-header evidence — pending push/deploy by owner
- [x] Canonical roadmap, decision register, packet, and local evidence updated

## 17. Implementation findings record (August 14, 2026)

### Supervisor contract decisions
- No Alembic migration required. Existing `validation_findings.observed`/`expected` JSONB, `state_events.reason_code` text, and revision tables are sufficient.
- Additive API contract: `GET /receipts/{id}` response gains `review_guidance` (nullable) and `validation_findings[].observed/expected`; `POST /human-revisions` gains `review_disposition` (default `"corrected"` — fully backward-compatible).
- `DraftPatch`, `ReviewCandidate`, `ReviewGuidance` schemas added to OpenAPI as new component schemas. No existing schemas modified.

### Agent A findings (Backend)
- Fixed `_simulate_and_score`: originally counted FAIL→NOT_APPLICABLE as "restored"; corrected to count only FAIL→PASS transitions, ensuring Rule 6 (remove_line_item) only fires when removal genuinely makes a material check pass.
- `_snapshot_equals_parent` compares the complete editable snapshot, including exact-decimal line fields and purchase instant/timezone; the client constructs that snapshot from raw and normalized parent values without fabricating defaults.
- `LINE_ITEMS_TO_SUBTOTAL_V1` added as 4th check in `run_deterministic_checks`; uses gross-sum-OR-net-sum pass logic with 1-minor-unit tolerance.
- Partial line-item monetary coverage produces `NOT_APPLICABLE` and cannot drive a subtotal proposal.

### Agent B findings (Frontend)
- `ValidationGuidance.tsx` uses no `dangerouslySetInnerHTML`; all text escaped. It formats the candidate amount, explains the reason, distinguishes ambiguity, and exposes the three approved actions.
- Live arithmetic preview in `HumanReviewForm` shows computed total vs. entered total on every field change; displays signed difference when mismatched.
- Applying a proposal focuses and scrolls to the affected receipt or line-item control.
- `confirmed_as_shown` flow handled entirely in `ReceiptDetail.tsx`; `HumanReviewForm` always submits as `"corrected"` disposition.
- Secondary candidates rendered below top candidate with individual "Apply" buttons.

### Agent C findings (Security/Verification)
- `_snapshot_equals_parent` tests cover every editable top-level and line-item field, equivalent decimal scales, changed purchase instants, and timezone semantics.
- `test_candidate_ranking.py` independently verified: no receipt text in `reason_codes`, `equations_before`, `equations_after`; at-most-3 constraint; signed delta sign; Rule 4/5/6 candidate generation.
- Integration tests `test_human_revision_disposition.py` specify full DB-level contract for all 5 scenarios; require `DATABASE_URL` to execute.
- Registered `security` pytest marker in `pyproject.toml` (required by `--strict-markers`).

### Residual risks
1. **No production deploy executed yet** — GitHub CI, production deployment, privacy-safe smoke, and owner acceptance remain the release gates.
2. **Unique two-line proposal deferred** — safe support needs explicit multi-target evidence and UX. The observed discount workflow and all one-field/one-line hypotheses are complete; no open-ended subset search or speculative double deletion was introduced.

## 14. Troubleshooting and review limits

- Non-blocker: diagnose for at most 15 minutes, then document/defer and continue.
- Blocker: diagnose for at most 30 minutes or two materially different attempts,
  whichever occurs first, then stop and wait for the owner.
- No recursive review loops. One implementation pass, one independent audit, and
  one bounded fix/retest pass.
- Stop immediately for private-data exposure, unsafe authorization, evidence loss,
  destructive migration/infrastructure, or required scope expansion.

## 15. Stop point

Stop after the bounded feature is documented, verified, pushed, deployed, and the
privacy-safe production smoke passes. Do not begin another Sprint 2 reliability
feature, a new ingestion source, analytics, or the DollarTrace rename.

## 16. Approval

**Approved by:** Yemane
**Date:** August 14, 2026
**Conditions:** Research smart guidance before implementation; system performs the
amount/item search and proposes a quick confirmation path; confirm-as-shown remains
available; avoid troubleshooting loops; document decisions and development method.
