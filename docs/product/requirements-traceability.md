# Financial OS — Initial Requirements Traceability Matrix

**Status:** Proposed review baseline  
**Owner:** Yemane  
**Created:** August 12, 2026  
**PRD baseline:** `docs/product/PRD.md` — approved August 12, 2026

## 1. Purpose

This matrix connects approved product requirements to architecture, implementation work, and objective verification. It prevents requirements from being lost between product discovery and delivery.

`Day one` means the first production receipt-capture vertical slice. `Later` requirements remain in the roadmap and do not block day-one release unless explicitly marked.

## 2. Traceability rules

- Every blocking day-one requirement must have an automated check or documented product demonstration.
- A generated implementation does not satisfy a requirement until its evidence exists.
- If a requirement changes, update the PRD first, then this matrix, affected designs, tests, and execution packets.
- Test identifiers are planned identifiers until the corresponding test exists.
- Evidence involving real financial data remains private; public portfolio evidence uses synthetic fixtures.

## 3. Day-one functional requirements

| ID | Requirement | Source | Design owner | Planned verification | Release |
|---|---|---|---|---|---|
| AUTH-001 | Only the allowlisted owner can access private application functions. | PRD §12.7 | API/Auth | `IT-AUTH-001`: unlisted identity receives 403 | Day one |
| AUTH-002 | Use managed Google/federated authentication; do not store a custom password. | PRD §12.7 | PWA/Auth | Configuration inspection and successful Google sign-in demo | Day one |
| AUTH-003 | Preserve a secure device session so routine capture does not require repeated sign-in. | PRD §12.7 | PWA/Auth | Installed-PWA close/reopen test | Day one |
| AUTH-004 | The owner can invalidate previously issued application access. | PRD §12.7 | API/Auth | `IT-AUTH-004`: session-version invalidation rejects old token | Day one |
| PWA-001 | The capture client can be added to the iPhone Home Screen and opens as a standalone web app. | PRD §10 rule 11 | PWA | Real-device installation demonstration | Day one |
| CAP-001 | The primary screen exposes a camera-first single-photo path. | PRD §5.6, §13.1 | PWA | Real-device capture demonstration | Day one |
| CAP-002 | One receipt can contain multiple ordered images. | PRD §10 rule 12 | PWA/API/Data | `IT-CAP-002`: order survives upload and retrieval | Day one |
| CAP-003 | The user can preview, remove, retake, and add receipt images before submission. | Approved UX interpretation | PWA | Component tests and real-device demonstration | Day one |
| CAP-004 | Camera denial or incompatibility falls back to the photo library. | Usability requirement derived from PWA constraints | PWA | Real-device permission-denial test | Day one |
| REC-001 | Creating a receipt is idempotent for a client-generated submission key. | PRD §6, roadmap delivery rule 5 | API/Data | `IT-REC-001`: repeated create request returns same receipt | Day one |
| UPL-001 | Each image uploads to a private object path authorized for that receipt only. | PRD §12.7 | API/Storage | `IT-UPL-001`: expired or wrong-object upload rejected | Day one |
| UPL-002 | The server validates object count, order, MIME type, size, and existence before acknowledgement. | PRD §12.7, §13.1 | API/Storage | `IT-UPL-002`: invalid evidence set cannot finalize | Day one |
| UPL-003 | Acknowledgement means the evidence and receipt metadata are durably stored. | PRD §11.5 | API/Data/Storage | `IT-UPL-003`: acknowledged receipt survives service restart | Day one |
| UPL-004 | Partial upload failure can retry missing images without duplicating completed images. | Reliability requirement | PWA/API | `IT-UPL-004`: resume incomplete evidence set | Day one |
| QUE-001 | An acknowledged receipt is durably queued for asynchronous extraction. | PRD §13.1 | API/Queue | `IT-QUE-001`: queue task exists after finalization | Day one |
| QUE-002 | Processing retries are idempotent and cannot create duplicate current results. | PRD §6, roadmap delivery rule 5 | Worker/Data | `IT-QUE-002`: same task executed twice yields one current revision | Day one |
| EXT-001 | The extractor accepts one or more ordered receipt images through a provider-neutral interface. | PRD §5.7, §10 rule 12 | Worker/AI | Unit contract test with fake provider | Day one |
| EXT-002 | Extraction returns merchant, purchase date, subtotal, tax, tip, discount, total, currency, and line items when evidenced. | PRD §13.1 and source handoff | Worker/Domain | Schema tests and fixture evaluation | Day one |
| EXT-003 | Each line item can preserve raw description, normalized description, quantity, unit, unit price, line total, discount, category suggestion, and field confidence. | PRD §5.3 and source handoff | Domain/Data | Schema round-trip test | Day one |
| EXT-004 | Provider, model, prompt, schema, timing, raw output, and error provenance are retained for each extraction attempt. | PRD §12.6, §12.8 | Worker/Data | `IT-EXT-004`: extraction-run record completeness | Day one |
| VAL-001 | Model output cannot enter queryable structured records unless it passes schema validation. | PRD §5.5, §12.8 | Domain | Unit tests with malformed outputs | Day one |
| VAL-002 | Deterministic checks evaluate required fields and receipt arithmetic using decimal/fixed-point money. | PRD §5.5, §12.8 | Domain | Unit tests for totals, tolerance, weighted items, discounts | Day one |
| VAL-003 | Validation produces explicit system-validated or needs-review evidence; it never silently repairs source values. | PRD §12.8 | Domain/Data | State-transition and audit tests | Day one |
| STATE-001 | Processing and verification use independent state dimensions. | PRD §12.8 | Domain/Data/API | State-machine unit tests and API schema inspection | Day one |
| STATE-002 | Every acknowledged receipt reaches `extracted`, `needs_review`, or `failed`; stuck work is measurable. | PRD §11.5 | Worker/Ops | Integration test plus age metric | Day one |
| VIEW-001 | Minimal history shows each receipt and current processing/verification status. | PRD §13.1 | PWA/API | End-to-end browser test | Day one |
| VIEW-002 | Receipt detail exposes ordered evidence and current structured result. | PRD §13.1 | PWA/API | End-to-end browser test | Day one |
| RET-001 | V1 does not automatically delete original receipt images. | PRD §12.6 | Storage/Infra | Bucket lifecycle configuration test | Day one |
| RET-002 | Structured records, extraction history, and provenance are durable and exportable. | PRD §12.6, §12.12 | Data/API | Export/backup smoke test | Day one |

## 4. Day-one quality and security requirements

| ID | Requirement | Source | Planned verification | Release |
|---|---|---|---|---|
| REL-001 | Zero acknowledged receipts may be lost. | PRD §11.5 | Failure-injection test and daily loss counter | Day one |
| REL-002 | At least 95% of release-test receipts complete processing within two minutes. | PRD §11.5 | Timed synthetic/private fixture run | Day one |
| REL-003 | Every failure is explicit, observable, and retryable where safe. | PRD §11.5 | Forced provider and worker failure tests | Day one |
| PERF-001 | Normal single-photo capture and submission completes within ten seconds, excluding processing, under documented conditions. | PRD §11.5 | Real-device timed test on Wi-Fi and cellular | Day one |
| SEC-001 | Transport uses HTTPS; storage and database encryption at rest remain enabled. | PRD §12.1–12.3 | Deployment configuration inspection | Day one |
| SEC-002 | Buckets and database are not public. Evidence retrieval uses owner authorization or short-lived capability URLs. | PRD §12.2 | Public-access negative tests | Day one |
| SEC-003 | Secrets use managed identity or Secret Manager and never enter source control. | PRD §6, §12.2 | Secret scan and IAM inspection | Day one |
| SEC-004 | Public endpoints enforce authentication, authorization, size/type limits, and privacy-safe audit events. | PRD §12.7 | Integration and log-content tests | Day one |
| SEC-005 | The processing worker accepts only authenticated queue invocations. | Threat-model requirement | Direct unauthenticated worker call rejected | Day one |
| SEC-006 | Receipt text is treated as untrusted data and cannot issue instructions or gain tools. | Blueprint §13 | Adversarial receipt fixture test | Day one |
| SEC-007 | Application logs exclude images, receipt content, auth tokens, signed URLs, and restricted identifiers. | PRD §12.2–12.3 | Log snapshot test and manual review | Day one |
| SUP-001 | CI runs tests, static checks, dependency checks, and secret/private-data scanning. | PRD §6 | Required GitHub Actions checks | Sprint 0 |
| PORT-001 | API, domain logic, schema, and extraction interface remain portable outside the initial cloud. | PRD §5.7, §12.12 | Container build plus provider-adapter boundaries | Day one |
| A11Y-001 | Capture flow uses accessible names, visible focus, adequate contrast, large touch targets, and non-color-only status. | Quality standard | Automated accessibility scan and real-device review | Day one |

## 5. First-30-day and later requirements

| ID | Requirement | Source | Planned verification | Release |
|---|---|---|---|---|
| OPS-030-001 | At least 95% of submitted receipts complete without system failure. | PRD §11.5 | 30-day service metric | Sprint 2 |
| OPS-030-002 | At least 90% of totals reconcile or are correctly marked for review. | PRD §11.5 | Verified sample comparison | Sprint 2 |
| OPS-030-003 | Fewer than 1% of jobs remain unresolved beyond ten minutes. | PRD §11.5 | Job-age metric | Sprint 2 |
| EVAL-001 | Establish a manually verified set of at least 50 varied receipts before field-accuracy targets. | PRD §11.5 | Versioned private evaluation manifest | Sprint 2 |
| TXN-001 | Import Capital One Venture X and Ally personal transactions from January 1, 2026 onward. | PRD §12.9–12.10 | Import reconciliation tests | Sprint 3 |
| TXN-002 | Credit-card payments and owned-account transfers are not double-counted. | PRD §10 | Deterministic financial-rule tests | Sprint 3 |
| RENT-001 | Coarsely classify identifiable rental-related shared-card transactions and exclude them from personal behavior metrics. | PRD §12.11 | Filter and aggregate tests | Sprint 3–4 |
| MATCH-001 | Match receipts and transactions without assuming a one-to-one relationship. | PRD §9 | Candidate and confirmed-match tests | Sprint 4 |
| RECON-001 | Reconcile 100% of available in-scope account-month statements. | PRD §11.5 | Account-month reconciliation report | Sprint 4 |
| COV-001 | Reach at least 99% financial coverage for in-scope personal accounts. | PRD §11.5 | Coverage metric with versioned denominator | Sprint 4 |
| COV-002 | Reach at least 80% eligible itemization coverage, improving toward 95%. | PRD §11.5 | Itemization metric with evidence eligibility rules | Sprint 5+ |
| SRC-001 | Amazon, Costco, email, statements, pay stubs, and utilities begin with manual fallbacks and later gain source adapters. | PRD §12.10 | Adapter contracts and source-specific tests | Sprint 3–6 |
| PAY-001 | Pay-stub detail reconciles gross pay, deductions, taxes, benefits, and net deposit without storing restricted identifiers in analytics. | PRD §4, §12.3 | Sanitization and reconciliation tests | Sprint 6 |
| LLM-001 | The future local model queries only an allowlisted read-only finance service and cannot move money or access credentials. | Blueprint §§9–10 | Tool authorization and network-isolation tests | Sprint 8 |

## 6. Day-one design and execution mapping

Every day-one row maps through its requirement family below. Section references identify the review-baseline design; target test locations become exact files during implementation.

| Requirement family | Architecture/control owner | Execution workstream | Target verification location |
|---|---|---|---|
| AUTH-* | `system-architecture.md` §§4.1–4.2, 9; `threat-model.md` T-01/T-02; controls IAM-01–03 | Contract lead, PWA, receipt service | `tests/integration/auth/`, `apps/web/**/__tests__/auth*`, real-device acceptance |
| PWA-*, CAP-* | `day-one-ux.md` §§3–5, 7–9; `system-architecture.md` §4.1 | Mobile PWA | `apps/web/**/__tests__/capture*`, `tests/e2e/capture/`, real-device acceptance |
| REC-* | `system-architecture.md` §§5–6; `data-architecture.md` §§2, 6, 9; API-02 | Receipt service | `tests/integration/receipts/test_create_idempotency*` |
| UPL-* | `system-architecture.md` §§4.2, 4.5, 5–6; `threat-model.md` T-03/T-04; OBJ-01–04 | PWA, receipt service, platform | `tests/integration/storage/`, `tests/e2e/upload/` |
| QUE-* | `system-architecture.md` §§4.3, 4.6, 5–6; `data-architecture.md` §6; QUE-01/02 | Receipt service, platform | `tests/integration/queue/`, failure-injection suite |
| EXT-* | `system-architecture.md` §§4.3, 4.7; `data-architecture.md` §§4.4–4.7; AI-01/02 | Receipt service | `tests/contract/extraction/`, private benchmark report |
| VAL-* | `system-architecture.md` §4.3; `data-architecture.md` §§2, 4.6–4.8, 7–8; AI-03/DB-02 | Receipt service | `tests/unit/domain/test_validation*`, receipt regression fixtures |
| STATE-* | `system-architecture.md` §§6, 10; `data-architecture.md` §§4.9, 5–6; QUE-02/LOG-02 | Receipt service, platform | `tests/unit/domain/test_states*`, `tests/integration/processing/` |
| VIEW-* | `day-one-ux.md` §§4.6–4.7; `system-architecture.md` §§4.1–4.2, 7 | Mobile PWA, receipt service | `tests/e2e/history_detail/` |
| RET-* | `system-architecture.md` §11; `data-architecture.md` §§4, 12; OBJ-04/DB-03 | Receipt service, platform | `tests/integration/export/`, restore and lifecycle evidence |
| REL-* | `system-architecture.md` §§6, 10–11; `data-architecture.md` §6; API-03/QUE-02/DB-03/OPS-01 | Receipt service, platform, integration lead | `tests/failure_injection/`, release metrics, restore record |
| PERF-* | `day-one-ux.md` §6; `system-architecture.md` §§5, 10 | PWA, platform | Real-device timed acceptance and processing benchmark |
| SEC-* | `system-architecture.md` §9; all `threat-model.md` boundaries; applicable `control-baseline.md` MUST controls | All, security reviewer | `tests/security/`, policy/IAM/header/log evidence |
| SUP-* | `system-architecture.md` §11; `technology-recommendation.md` §4.7; CICD-01–03 | Platform/verification | `.github/workflows/` required-check evidence |
| PORT-* | `system-architecture.md` §§8, 12; `technology-recommendation.md` §§2, 4 | Contract lead, receipt service | container smoke test and dependency-boundary inspection |
| A11Y-* | `day-one-ux.md` §7 | Mobile PWA | automated accessibility scan plus real-device review |

The authoritative work breakdown and acceptance-evidence rollup are in `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md` §§9 and 12.

## 7. Traceability completion during implementation

- Replace target test locations with exact files and CI evidence as they are created.
- Add the frozen commit, image digest, deployed revision, device conditions, and private acceptance-record reference.
- Resolve any reviewer finding that reveals an untraceable blocking requirement.
- Record exceptions as owner-approved decisions; do not silently downgrade requirements.
