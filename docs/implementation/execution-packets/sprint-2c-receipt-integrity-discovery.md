# Execution Packet — Sprint 2C Receipt Integrity and Discovery

**Status:** Approved for implementation  
**Packet owner:** Yemane  
**Operating lead:** Codex  
**Implementation lead:** Claude Code through Vertex AI  
**Date:** August 15, 2026  
**Repository revision:** `ce10ed1`

## 1. Outcome

The owner can keep scanning current and historical receipts without silently
creating duplicate financial records, and can find any receipt quickly by
merchant, item, purchase date, amount, verification state, processing state, or
duplicate state without scrolling through the full history.

## 2. Product principles

- Duplicate detection is an independent state axis. A receipt can be
  successfully extracted and also be a duplicate.
- Every uploaded artifact remains preserved. Duplicate classification never
  deletes, overwrites, or silently merges evidence.
- Discovery operates over the complete owner-scoped dataset on the server, not
  only the cards currently loaded in the browser.
- The existing receipt-card presentation remains the primary result view.
- Historical receipts are organized by effective purchase date, not the date on
  which an old receipt happened to be uploaded.
- Deterministic rules perform duplicate classification. No language model
  calculates a fingerprint or authorizes a duplicate decision.

## 3. Canonical inputs

- `AGENTS.md`
- `CLAUDE.md`
- `docs/product/PRD.md`
- `docs/product/roadmap.md`
- `docs/product/open-items-and-decisions.md`
- `docs/architecture/data-architecture.md`
- `docs/architecture/implementation-contracts.md`
- `docs/security/control-baseline.md`
- `docs/governance/ai-development-operating-model.md`
- `docs/implementation/execution-packets/sprint-2a-human-review.md`
- `docs/implementation/execution-packets/sprint-2b-smart-validation-guidance.md`

This packet and those canonical artifacts are authoritative. Conversation
history is supporting context only.

## 4. Accepted duplicate-detection contract

Add a third independent receipt state axis:

```text
unchecked -> unique | suspected_duplicate | confirmed_duplicate
```

The current projection records:

- `deduplication_status`;
- `canonical_receipt_id`, nullable and owner-scoped;
- `evidence_fingerprint`, nullable SHA-256 over a versioned canonical ordered
  asset-hash manifest that excludes storage object paths;
- `semantic_fingerprint`, nullable SHA-256 over versioned canonical normalized
  receipt fields;
- `deduplication_method`, nullable privacy-safe rule identifier;
- `deduplication_rule_version`, nullable;
- `deduplication_checked_at`, nullable.

The append-only state-event stream adds the `deduplication` dimension. Reason
codes contain no merchant, item, amount, hash, owner identity, or receipt text.

Rules, in priority order:

1. Existing owner/client-submission idempotency returns the same receipt.
2. Exact ordered evidence fingerprint match confirms a duplicate.
3. A complete exact semantic signature may confirm a separately photographed
   receipt only when normalized merchant, purchase instant, currency, total, and
   complete normalized line-item multiset all agree.
4. Incomplete or looser structured agreement yields `suspected_duplicate` only.
5. Otherwise the receipt is `unique`.

The canonical receipt is the earliest valid acknowledged root receipt using a
deterministic timestamp and UUID tie-break. A canonical pointer never forms a
self-link, cycle, or duplicate chain. Classification is owner-scoped and
idempotent. Human correction recomputes the semantic result. An idempotent
backfill evaluates existing receipts and converges any concurrent edge case.

## 5. Accepted discovery contract

The Receipts view adds:

- a pinned `Search merchant or item` field;
- quick filters for needs-review, duplicates, and verified receipts;
- a filter sheet for effective purchase-date range, amount range, processing
  status, verification status, duplicate status, and sort order;
- removable active-filter chips and a clear-all action;
- total result count;
- purchase-month grouping;
- a matched-line-item explanation when an item description caused the match;
- contextual loading, error, and no-results states;
- restoration of search, filters, loaded cursor pages, and scroll position when
  returning from receipt detail.

Effective receipt date is `purchase_datetime`, then `captured_at`, then
`created_at`. Default ordering is effective date descending with receipt UUID as
the stable tie-break. Explicit `Load more` cursor pagination remains; infinite
scroll and offset pagination are not introduced.

Search runs as an authenticated owner-only request with its term in a JSON body
so merchant or item terms do not enter infrastructure request-URL logs:

```text
POST /api/v1/receipts/search
```

The bounded request accepts `query`, date bounds, amount bounds, processing,
verification and duplicate status arrays, `sort`, `cursor`, and `limit`. The
response returns receipt cards, `total_count`, and `next_cursor`. Search terms
are case-insensitive, Unicode-normalized, parameterized, length-bounded, and
matched against the current normalized merchant and canonical line-item
descriptions. Raw OCR/provider output is not searched.

## 6. Scope

- Add the additive database migration, indexes, model fields, state enum, and
  privacy-safe events for duplicate classification.
- Add deterministic exact and semantic fingerprinting plus canonical selection.
- Run classification after finalization, successful extraction, and human
  correction at the earliest point each signal is available.
- Add a dry-run-capable idempotent duplicate backfill and production runbook.
- Add owner-only server-side receipt search and stable keyset pagination.
- Remove the current N+1 current-revision query from receipt listing/search.
- Add the mobile-first discovery interface while preserving existing cards.
- Add backend, migration, contract, frontend, accessibility, security,
  concurrency, backfill, and regression tests.
- Update roadmap, decision register, OpenAPI artifacts, evidence, and operations.

## 7. Non-goals and stop boundary

- Evidence deletion, automatic merge, or destructive duplicate cleanup
- Perceptual image hashing, computer-vision similarity, or learned thresholds
- Saved searches, search history, advanced query language, or natural-language
  finance questions
- Categories, dashboards, analytics, exports, or bulk actions
- Receipt-to-bank/Amazon/email/Costco matching
- Plaid, statements, transactions, payroll, or rental-property itemization
- DollarTrace repository/infrastructure rename
- Native SwiftUI work

Record useful discoveries as follow-ups; do not expand this sprint.

## 8. Parallel workstreams and file ownership

| Workstream | Owner | Primary boundary | Deliverable |
|---|---|---|---|
| Contract/integration | Codex | Packet, shared contract, integration, release evidence | Frozen contract and coherent release |
| A — Integrity | Sonnet A | Domain/model/migration/worker/backfill/backend tests | Deterministic deduplication engine |
| B — Discovery | Sonnet B | New search service/route/schema, PWA/API client/styles/tests | Server-side receipt discovery experience |

Workstream A owns migration `002` and may change receipt/state models. Workstream
B must not create a migration and should place backend search behavior in new
search-specific modules where practical. Shared schema/router/model integration
belongs to Codex. Agents use isolated worktrees, synthetic fixtures, and commits.

## 9. Acceptance evidence

| Requirement | Verification |
|---|---|
| Submission replay | Same owner/submission returns one logical receipt |
| Exact duplicate | A separately submitted identical asset set becomes confirmed and links to the canonical root |
| Separate photograph | Complete identical semantic evidence is detected; incomplete evidence is only suspected |
| False-positive safety | Same merchant/amount on different dates remains unique; ambiguous same-day evidence is not auto-confirmed |
| Preservation | Original and duplicate evidence/revisions remain retrievable and unchanged |
| Correction | Human revision reruns semantic classification without mutating prior evidence |
| Backfill | Dry run reports privacy-safe counts; repeated apply produces the same state |
| Search completeness | Merchant and item queries search beyond the first page and remain owner-scoped |
| Historical order | Old receipts appear by purchase date, with captured/upload fallback clearly represented |
| Combined filters | Query, date, amount, state, duplicate status, sort, and pagination compose correctly |
| Stable paging | No duplicates or omissions across cursor pages with equal timestamps |
| Navigation | Back from detail restores filters, loaded results, and scroll position |
| Accessibility | Labeled search, keyboard operation, visible focus, 44px targets, and live result status |
| Privacy/security | Search terms/content/hashes never enter application logs; cross-owner access returns nothing |
| Regression | Capture, extraction, correction, retry, detail, auth, HEIC, PWA, and CI remain green |

## 10. Operational and security constraints

- No real receipt content, values, images, hashes, owner identifiers, project
  identifiers, or signed URLs enter source, prompts, tests, logs, CI, or public
  evidence.
- The search and duplicate services begin every query with the authenticated
  owner boundary; candidate and canonical receipts must share that owner.
- Fingerprints are evidence signals, not authentication secrets, and are never
  returned by public APIs.
- The backfill defaults to dry-run, emits aggregate privacy-safe counts, supports
  bounded batches, and is safe to resume.
- Expand-contract deployment order is migration, API/worker, backfill, PWA, then
  smoke tests. Rollback preserves the additive columns and all evidence.

## 11. Troubleshooting boundary

For any one issue, investigate for at most 30 minutes. If non-blocking, record it
and continue. If it blocks safe migration, owner isolation, evidence preservation,
classification correctness, search correctness, build, deployment, or production
readiness, stop and return the exact evidence to the owner. Do not enter an
unbounded debugging loop.

## 12. Sprint stop line

Stop after both features are deployed privately, the duplicate backfill is
validated, complete local/CI gates are green, privacy-safe production smoke tests
pass, and canonical documentation/evidence is current. Owner real-receipt
acceptance may follow; do not begin saved search, analytics, matching, new data
sources, perceptual hashing, or rename work in this sprint.

## 13. Approval

**Product/design approval:** approved by Yemane on August 15, 2026  
**Implementation authorization:** approved — “approved. go!”  
**Conditions:** preserve the established security/durability standards, run the
two implementation streams independently where their file boundaries permit,
and enforce the 30-minute troubleshooting rule.
