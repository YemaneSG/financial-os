# Financial OS — Outcome Roadmap

**Status:** Approved sequencing baseline  
**Owner:** Yemane  
**Created:** August 12, 2026  
**Last updated:** August 12, 2026

## 1. Purpose

This roadmap turns the Financial OS product vision into small, usable vertical slices. It preserves important future capabilities without making them prerequisites for beginning data acquisition.

The roadmap is model-agnostic and outcome-oriented. Sprint numbers describe sequence, not fixed calendar duration. Dates and estimates will be added after product discovery establishes the remaining integration and operational constraints.

## 2. Delivery rules

1. Every sprint must produce a demonstrable user or operational outcome.
2. Receipt acquisition continues while later capabilities are developed.
3. Each ingestion source implements a stable source-adapter contract rather than changing the canonical financial model.
4. Raw evidence, normalized records, provenance, and processing versions remain distinguishable.
5. Imports must be retryable and idempotent before they are automated on a schedule.
6. New automation begins with observable manual execution and a documented fallback.
7. Security, privacy, tests, documentation, and operational readiness are part of the work—not a final hardening phase.
8. A sprint exit requires evidence against its acceptance criteria, not merely completed code.

## 3. Capability sequence

### Sprint 0 — Model-agnostic project foundation

**Outcome:** Contributors can understand, run, test, and extend the project safely.

**Scope:**

- Adapt the AI Project Blueprint without inheriting tool-specific assumptions as canonical rules.
- Establish model-agnostic contributor instructions and retain optional tool adapters.
- Initialize version control and a feature-branch workflow.
- Create the Python environment, package skeleton, test runner, linting, and continuous integration.
- Establish secret scanning, dependency updates, synthetic fixtures, and private-data exclusions.
- Record the initial architecture, threat model, data classification, and Architecture Decision Records.

**Exit evidence:**

- A fresh clone can be configured and tested from documented instructions.
- CI verifies the foundation.
- The repository contains no real financial data, PII, or credentials.

### Sprint 1 — One-day receipt capture vertical slice

**Outcome:** Daily data acquisition begins from an iPhone.

**Scope:**

- Installable mobile-first Progressive Web App
- Camera-first receipt capture with a single-photo fast path
- Optional ordered multi-photo capture for long or difficult receipts
- Allowlisted single-user managed authentication with a persistent secure device session
- Authenticated upload and acknowledgement
- Durable image and metadata storage
- Automatic receipt and line-item extraction
- Schema and arithmetic validation
- Structured persistence
- Processing status and minimal receipt history/detail
- Critical-path automated tests

**Exit evidence:**

- A real single-image or multi-image receipt can travel from iPhone capture to persisted structured data.
- The original evidence and extraction provenance can be retrieved.
- Failure states are visible and retryable rather than silent.
- The day-one release targets defined in the PRD are demonstrated under documented test conditions.

### Sprint 2 — Acquisition reliability and human correction

**Outcome:** Receipt capture is trustworthy enough for sustained daily use.

**Scope:**

- Background retry and offline-aware queueing beyond the day-one partial-upload retry
- Image-quality checks and duplicate upload detection
- Confidence and review policy
- Minimal review queue and correction workflow
- Correction history and extractor-version tracking
- Privacy-safe operational metrics
- Configurable receipt retention controls without automatic deletion in V1
- Fixed receipt regression set

**Exit evidence:**

- Low-confidence or arithmetically inconsistent receipts are marked for review without blocking continued capture.
- System-validated and human-verified records remain distinguishable in storage and analysis.
- Corrections preserve the original extraction and become auditable training or evaluation evidence.
- The regression set measures extraction changes over time.

### Sprint 3 — Personal transaction and statement spine

**Outcome:** Financial money movement from January 1, 2026 onward is available independently of receipt capture.

**Scope:**

- Connector evaluation and approved read-only integration path
- Capital One Venture X transactions
- Ally personal checking transactions
- Manual import fallback for supported export formats
- Pending-to-posted lifecycle handling
- Transfer recognition, including credit-card payments
- Statement upload, sanitization, checksums, and archive metadata
- Account aliases and coarse exclusion of rental-related shared-card charges from personal analysis

**Exit evidence:**

- In-scope history is imported without unexplained duplicates.
- Credit-card payments and owned-account transfers are not double-counted.
- Monthly source statements are preserved and discoverable.
- Historical line items exist only where source evidence supports them; unitemized transactions remain explicit.

### Sprint 4 — Matching and statement reconciliation

**Outcome:** Money movement and purchase evidence form one explainable financial record.

**Scope:**

- Receipt-to-transaction candidate matching
- Many-to-many evidence relationships
- Match confidence and human confirmation
- Refund, reversal, split-charge, and restaurant-tip cases
- Account-month reconciliation workflow
- Financial coverage and statement-reconciliation metrics
- Unmatched transaction and unmatched evidence queues

**Exit evidence:**

- A captured receipt can be traced to the correct posted transaction.
- Every aggregate can expose its underlying evidence.
- Reconciliation reports explain discrepancies rather than hiding them.

### Sprint 5 — Commerce and email ingestion

**Outcome:** High-value purchases are itemized without relying exclusively on photographed receipts.

**Scope:**

- Amazon order, shipment, charge, return, and refund ingestion
- Email receipt forwarding or approved mailbox ingestion
- Costco history ingestion
- Source-specific parsing behind common ingestion contracts
- Cross-source duplicate detection
- Eligible purchase itemization coverage metric

**Exit evidence:**

- Amazon's non-one-to-one relationships among orders, shipments, charges, and refunds are represented correctly.
- Multiple sources can enrich one purchase without creating duplicate expenses.

### Sprint 6 — Payroll and recurring bills

**Outcome:** Income and specialized recurring financial activity are represented beyond bank descriptions.

**Scope:**

- Pay-stub ingestion and PII sanitization
- Gross pay, taxes, deductions, benefits, and net-pay reconciliation
- Utility bill ingestion
- Recurring-obligation detection

**Exit evidence:**

- Net payroll deposits reconcile to sanitized pay-stub details.
- Expected recurring activity can be compared with observed activity.

### Future capability — Rental operations

**Status:** Deferred; not scheduled in the initial personal-finance roadmap.

When intentionally introduced, this capability may add the Ally rental account, rental income and expense attribution, and property or unit aliases. Existing spreadsheet workflows remain authoritative until then. The shared-card financial-context boundary prevents rental-related charges from contaminating personal analysis in the meantime.

### Sprint 7 — Deterministic analytics and behavior dataset

**Outcome:** Captured history supports trustworthy analysis before conversational AI is added.

**Scope:**

- Spend by product, category, merchant, account, and time period
- Purchase frequency and price-change analysis
- Data-quality and coverage dashboards
- Behavior-analysis-ready features with documented definitions
- Provenance for every result
- Exportable analysis datasets

**Exit evidence:**

- Representative financial questions are answered deterministically.
- Results match reconciled source records and reveal supporting transactions and line items.

### Sprint 8 — Private read-only financial copilot

**Outcome:** A local model can explain grounded financial results without receiving financial authority.

**Scope:**

- Allowlisted read-only finance query service
- Local model selection and evaluation on Mac Mini hardware
- Network isolation and tool restrictions
- Prompt-injection resistance for untrusted financial content
- Grounded answers with calculations and source provenance
- Ambiguity, uncertainty, and refusal behavior

**Exit evidence:**

- The model cannot access credentials, arbitrary SQL, write operations, the public internet, or money-moving tools.
- Answers match deterministic reports and identify their evidence.

### Sprint 9 — Operational hardening and portfolio presentation

**Outcome:** Financial OS is recoverable, maintainable, and demonstrable without exposing personal data.

**Scope:**

- Mac Mini deployment and service isolation
- Encrypted backups and tested restoration
- Health checks, alerts, and incident response
- Connector revocation and disaster-recovery procedures
- Performance, accessibility, and security verification
- Synthetic demonstration dataset and architecture case study
- Public code/private data boundary review

**Exit evidence:**

- A documented restoration test succeeds.
- The public repository and portfolio demonstration contain only approved public artifacts.
- The system's quality claims are supported by tests, metrics, and operational evidence.

## 4. Cross-cutting capability lanes

The sprints advance four continuous lanes:

| Lane | Responsibility |
|---|---|
| Acquisition | Capture evidence and import external financial sources |
| Data trust | Validate, normalize, match, reconcile, and preserve provenance |
| Safety and operations | Protect data, observe failures, back up, restore, and respond |
| Intelligence | Progress from deterministic reports to a restricted local copilot |

Work in one lane should consume stable contracts from another. A later lane must not require rewriting an earlier acquisition source.

## 5. Planning cadence

Before starting a sprint:

- Confirm the user outcome and measurable exit criteria.
- Resolve only decisions that block that sprint.
- Break the sprint into the smallest testable vertical slices.
- Identify security and data migration implications.

At sprint completion:

- Demonstrate the outcome with synthetic or privately controlled data.
- Run automated checks and review security-sensitive changes.
- Record metrics, known limitations, and operational instructions.
- Update the PRD, roadmap, open items, and relevant ADRs.
- Select the next outcome using observed product and data-quality evidence.

## 6. Current status

- Initial PRD discovery is complete.
- The day-one receipt capture vertical slice is approved.
- The evidence-only historical backfill policy is approved.
- The initial cloud deployment and incremental Mac Mini transition are approved.
- Requirements traceability, UX, architecture, threat model, control baseline, and the Sprint 0/1 execution packet are prepared as `planning-baseline-2026-08-12-r1`.
- The planning baseline is ready for three independent Gate A reviews.
- Implementation has not started.
- Sprint numbers remain outcome sequence labels; Sprint 0/1 is targeted for one focused implementation session after Gate A and access preflight.
