# Financial OS — Product Requirements Document

**Status:** Approved baseline  
**Owner:** Yemane  
**Created:** August 12, 2026  
**Last updated:** August 12, 2026

## 1. Purpose

This document defines the product requirements for Financial OS. It is intentionally model-agnostic: any human contributor or AI-assisted development tool should be able to understand the product, its accepted decisions, its constraints, and its unresolved questions from the repository documentation.

This is a living document while product discovery is in progress. Accepted requirements are distinguished from preliminary recommendations and open decisions.

## 2. Product statement

> Account for every dollar and itemize every purchase wherever item-level evidence exists.

Financial OS will be a private personal financial information system and copilot. It will acquire financial records from multiple authorized sources, preserve raw evidence, normalize and reconcile those records, and eventually provide private, grounded financial analysis through a locally hosted language model.

It is not merely a budgeting application or receipt scanner. Its durable product asset is a trustworthy, auditable financial history that connects money movement to the underlying purchases and supporting evidence.

## 3. Primary user and context

The initial product is single-user software for Yemane.

Current context:

- A Mac Mini intended to host the long-term system is expected near the end of September 2026.
- Data acquisition should begin before that hardware is available.
- Approximately 80% of spending is charged to a Capital One Venture X credit card.
- Ally personal checking is used for payroll deposits, rent, credit-card payments, and selected bills.
- A separate Ally checking account is used for rental-property activity, but that account and its activity are outside the initial personal-finance release.
- Cash spending is negligible and does not justify early automation.
- Major itemization sources include H-E-B, Costco, Amazon, restaurants, and emailed receipts.
- Historical acquisition should begin with records from January 1, 2026 onward.
- Cloud storage and third-party processing are permitted for financial content, subject to the data-handling requirements in this document.
- The immediate delivery objective is a usable phone capture experience and working data backend within one focused day of implementation.
- Cost efficiency is important. Open-source and free-tier components are preferred when they satisfy the product, security, and operational requirements.

## 4. Product vision

Financial OS should develop into a durable financial memory that can:

- Explain where money came from and where it went.
- Trace material totals back to source transactions and evidence.
- Understand purchases at the item level when evidence permits.
- Reconcile transactions, receipts, orders, bills, and statements.
- Preserve a clean boundary between personal activity and the limited rental-related charges encountered on shared payment instruments.
- Describe payroll beyond the net deposit, including gross pay, taxes, deductions, and benefits when pay-stub evidence is available.
- Identify missing, unmatched, duplicated, reversed, refunded, or unusual activity.
- Help the user understand habits, priorities, goals, and tradeoffs without moralizing.
- Support deterministic reports and private natural-language questions.
- Remain useful when an external connector, model, or other replaceable provider is unavailable.

The immediate product objective is dataset creation rather than spending advice. Early releases should maximize reliable acquisition and preserve enough evidence for future longitudinal behavior analysis.

## 5. Product principles

### 5.1 Capture first, analyze second

Data acquisition must not wait for the complete intelligence layer. Raw evidence captured today can be reprocessed as extraction and normalization improve.

### 5.2 Build a transaction spine, then enrich it

Account and credit-card transactions establish that money moved. Receipts, orders, bills, pay stubs, and statements enrich that movement with itemization and context.

Neither transaction feeds nor purchase evidence is sufficient by itself.

### 5.3 Preserve raw and normalized values

Original descriptions, documents, source identifiers, and extraction outputs must be preserved according to the retention policy. Normalized values must not overwrite their source evidence.

### 5.4 Make provenance visible

Every material financial fact or aggregate should identify its sources, date range, filters, calculation method, reconciliation status, and relevant record identifiers.

### 5.5 Use deterministic financial calculations

Authoritative totals, matches, filters, and reconciliation results must be calculated by deterministic code using decimal or fixed-point money representations. A language model may interpret or explain results; it is not the calculator or ledger of record.

### 5.6 Minimize capture friction

Physical receipt capture should normally take approximately five to ten seconds:

```text
Open capture client
→ photograph receipt
→ submit
→ receive acknowledgement
→ leave
```

Correction, categorization, and review should not be mandatory during capture.

### 5.7 Keep providers replaceable

Connectors, OCR systems, language models, storage implementations, and user interfaces must interact through explicit contracts. Core financial meaning must not depend on a specific provider.

### 5.8 Separate analysis from authority

The future language model receives access only to an allowlisted, read-only query layer. It must not receive financial credentials, unrestricted database access, or the ability to initiate or approve financial actions.

### 5.9 Prefer appropriate simplicity

The project should use disciplined engineering without introducing infrastructure or abstraction before a demonstrated requirement exists.

### 5.10 Apply proportional data protection

Financial content may use cost-effective cloud storage and processing. Direct personal identifiers, credentials, connector secrets, and reusable financial identifiers require stricter handling. Permission to process data in the cloud is not permission to expose it publicly, retain it indefinitely, place it in logs, or include it in the public repository.

## 6. Quality standard

Financial OS is intended to be a production-minded personal system and a portfolio-quality demonstration of software engineering and technical product judgment.

The quality standard includes:

- Security and privacy designed into system boundaries, not added after implementation.
- Explicit domain rules and versioned data contracts.
- Threat modeling for financial data, credentials, untrusted documents, and AI-assisted querying.
- Automated unit, integration, regression, and security tests proportional to risk.
- Reproducible development and deployment environments.
- Schema migrations and backward-compatible evolution where appropriate.
- Observable ingestion with structured, privacy-safe logs and actionable failure states.
- Idempotent imports and explainable duplicate detection.
- Data retention, encrypted backup, and tested restoration procedures.
- Architecture Decision Records for consequential or difficult-to-reverse choices.
- Continuous integration, dependency management, secret scanning, and supply-chain controls.
- Synthetic or anonymized fixtures only in the public repository.
- Clear separation between public source code and private runtime data, secrets, documents, configuration, and deployment state.
- Documentation that is usable by humans and multiple AI development tools.

World-class quality does not require premature microservices, distributed infrastructure, or fashionable components. Claims of quality should be supported by tests, measurements, operational evidence, and clear design rationale.

## 7. Initial acquisition sources

| Source | Role | Initial acquisition intent |
|---|---|---|
| Capital One Venture X | Primary spending transaction spine | Acquire transactions and statements from January 2026 onward |
| Ally personal checking | Personal cash-flow spine | Acquire payroll, rent, transfers, card payments, and bills |
| Ally rental checking | Future rental-property transaction spine | Defer account acquisition until the rental capability is intentionally introduced |
| Physical receipts | Item-level purchase evidence | Capture from an iPhone with a single-purpose, low-friction client |
| H-E-B receipts | High-priority grocery itemization | Photograph receipts immediately after purchase |
| Costco receipts and purchase history | Mixed-basket itemization | Ingest available history and new receipts |
| Amazon order history | Online-order itemization | Ingest orders, shipments, charges, returns, and refunds |
| Email receipts | Supplemental itemization | Support forwarding or depositing receipts into an ingestion location |
| Monthly statements | Authoritative reconciliation evidence | Preserve original PDFs independently of connectors |
| Utility bills | Recurring-bill detail | Acquire charge detail and later usage data where valuable |
| Employer pay stubs | Income detail | Acquire gross pay, net pay, taxes, deductions, and benefits |
| Cash purchases | Low-volume exception | Support manual capture; no early automation requirement |

## 8. Acquisition strategy

### 8.1 Layer 1 — Transaction spine

Acquire transactions from the primary credit card, personal checking, and rental checking accounts. Preserve source identifiers, source account aliases, raw descriptions, dates, amounts, pending or posted state, import timestamps, and connector provenance.

### 8.2 Layer 2 — Authoritative records

Acquire and preserve monthly statements from January 2026 onward. Statements establish the reconciliation baseline used to evaluate completeness and correctness of connector and manual imports.

### 8.3 Layer 3 — Purchase itemization

Prioritize high-value and high-frequency itemization sources:

1. H-E-B physical receipts
2. Costco receipts and purchase history
3. Amazon orders, shipments, returns, and refunds
4. Email receipts
5. Restaurant and miscellaneous physical receipts

### 8.4 Layer 4 — Income and specialized records

Add employer pay stubs, rental-property records, utility bills, recurring obligations, and workflows for unmatched or missing evidence.

## 9. Core conceptual model

The product must distinguish money movement from supporting evidence.

```text
Financial transaction
        │
        ├── may match a receipt
        ├── may match an online order or shipment
        ├── may match a bill
        ├── appears on a statement
        └── may have no item-level evidence

Receipt or order
        │
        ├── may contain one or more ordered evidence assets
        ├── contains one or more line items
        ├── may be split across multiple charges
        ├── may participate in a return or refund
        └── may initially be unmatched
```

The domain model must eventually accommodate many-to-many relationships. One order is not assumed to equal one charge, and one transaction is not assumed to equal one document.

## 10. Canonical financial rules accepted so far

1. A purchase charged to a credit card is an expense. Paying the credit-card balance from checking is a transfer and must not be counted as another expense.
2. Transfers between accounts owned by the user are not income or expenses.
3. Payroll deposits are income, while pay stubs provide the detailed relationship among gross pay, taxes, deductions, benefits, and net pay.
4. Zelle rent deposits into the rental checking account are rental income, subject to later verification and property or unit attribution.
5. Refunds and reversals should be linked to their original purchases whenever possible.
6. Pending transactions and posted transactions are different lifecycle states and must not silently become duplicates.
7. A statement is authoritative monthly evidence; a connector feed is convenient operational data.
8. Merchant-level categories are insufficient for mixed baskets such as Costco or Amazon orders.
9. Restaurant authorization, receipt, tip, and final posted amount may differ and must be representable separately.
10. Cash spending is within the product vision but does not require automated acquisition in the initial release.
11. The first phone client will be an installable, mobile-first Progressive Web App. A native SwiftUI client may be added later against the same stable backend contracts.
12. A receipt may contain one or more ordered images. Single-photo capture remains the default fast path, while optional multi-photo capture supports long or difficult receipts.

## 11. Product success measures

### 11.1 Financial coverage

The percentage of in-scope money movement that is imported, classified by financial meaning, and accounted for without unexplained duplication.

The precise denominator, eligible states, and treatment of transfers will be defined before implementation.

### 11.2 Eligible purchase itemization coverage

The percentage of eligible purchase spending connected to sufficiently verified item-level evidence.

Eligibility must exclude transactions that do not naturally contain retail line items and must be defined explicitly before this metric is operationalized.

### 11.3 Statement reconciliation

The number and percentage of in-scope account-months successfully reconciled to authoritative statements.

### 11.4 Operational quality indicators

Supporting measures should include:

- Unmatched financial transactions
- Unmatched receipts, orders, bills, and pay stubs
- Records awaiting human review
- Duplicate or suspected-duplicate records
- Import failures and retry age
- Pending transactions that have not resolved normally
- Extraction and field-level accuracy on a fixed regression set
- Capture completion time and upload success rate
- Backup and restoration test status

Metric definitions and targets remain open PRD work.

### 11.5 Accepted initial success targets

#### Day-one release gate

- 100% of acknowledged uploads are durably stored and retrievable.
- Single-photo and ordered multi-photo receipts are supported.
- Every upload reaches an explicit `extracted`, `needs_review`, or `failed` outcome; silent failures are not permitted.
- At least 95% of the release test set completes processing within two minutes.
- Capture is verified over both Wi-Fi and cellular connectivity.
- The installed PWA completes the normal single-photo capture and submission workflow within ten seconds under the documented test conditions, excluding asynchronous backend processing.

#### First 30 days

- At least 95% of submitted receipts complete processing without a system failure.
- At least 90% of receipt totals either reconcile algorithmically or are correctly marked for review.
- Fewer than 1% of processing jobs remain unresolved for more than ten minutes.
- Zero acknowledged receipts are lost.
- A manually verified regression set of at least 50 varied receipts is established before field-level extraction-accuracy targets are finalized.

#### After transaction matching is available

- At least 99% financial coverage for in-scope personal accounts.
- 100% statement reconciliation for available in-scope account-months.
- At least 80% eligible purchase itemization coverage initially, improving toward 95%.
- Rental-classified charges are excluded from personal behavior metrics.

Test conditions, metric denominators, exclusions, and field-level extraction targets must be versioned with the evaluation plan so reported performance remains reproducible and comparable.

## 12. Accepted privacy, deployment, and cost boundary

### 12.1 Cloud use

Financial content such as receipts, transaction records, and statements may be stored or processed using cloud services. The architecture does not require local-only processing before the Mac Mini arrives.

Cloud components should be selected for the smallest combination of cost, implementation effort, reliability, portability, and security that satisfies the release requirements. Free and open-source components are preferred, but zero license cost does not override reliability, privacy, or operational fit.

### 12.2 Data classes

The initial data-handling model has three classes.

#### Restricted identifiers and secrets

At minimum:

- Social Security and other tax identification numbers
- Date of birth
- Home address
- Full bank-account and routing numbers
- Financial-institution credentials
- Connector credentials, access tokens, and refresh tokens
- Private keys, API keys, passwords, and session credentials

These values must not enter the general analytical store, ordinary application logs, model prompts, retrieval indexes, source control, test fixtures, screenshots, or portfolio material.

The complete restricted-field inventory will be finalized during threat modeling. Treating a value as restricted may be expanded later without changing the product architecture.

#### Private financial content

Examples include:

- Receipts and line items
- Transaction descriptions and amounts
- Statements after required identifier handling
- Payroll amounts, taxes, deductions, and benefits
- Rental income and expense records
- Purchase and merchant history

This content is permitted in approved cloud storage and processing systems. It still requires authentication, authorization, encryption in transit and at rest, private access controls, sanitized logs, retention rules, and exclusion from the public repository.

#### Public development artifacts

Examples include source code, schemas, architecture documentation, synthetic fixtures, and aggregate demonstrations that cannot identify the user or reconstruct private financial activity.

Only this class is eligible for the future public portfolio repository.

### 12.3 PII minimization and sanitization

Documents likely to contain restricted identifiers, including pay stubs and financial statements, require a PII-aware ingestion path.

The intended lifecycle is:

```text
Receive through a controlled boundary
→ detect restricted fields
→ extract required financial facts
→ redact or tokenize restricted values
→ validate sanitization
→ store sanitized structured data
→ delete, quarantine, or place the original in a separately controlled encrypted vault according to policy
```

Restricted identifiers must not be copied merely because they appear in a source document. A general-purpose cloud AI processor should receive a sanitized derivative when local or boundary redaction is necessary to enforce this rule.

The system must record the sanitizer version, processing result, and validation status without logging the restricted value itself. Sanitization failures must enter a quarantine state rather than the normal processing pipeline.

### 12.4 Delivery optimization

The first implementation should optimize for a usable phone capture path and data backend within one focused day. The accepted first client is an installable, mobile-first Progressive Web App that provides direct camera capture, optional multi-photo capture for long receipts, upload, and acknowledgement from an iPhone home-screen experience.

The capture and processing APIs must remain client-independent. A native SwiftUI application may later complement or replace the initial capture interface without requiring a new ingestion pipeline or financial data model.

The design should remain portable through stable interfaces and exportable data. Rapid implementation may choose managed services, but domain logic and durable records must not become inseparable from a single provider.

### 12.5 Available development resources

The user currently has access to ChatGPT Plus, Claude Pro, and Claude Code through Vertex AI. Before relying on any subscription for an application runtime, the project must verify its programmatic access, usage terms, privacy controls, limits, and incremental cost. A consumer or development subscription must not be assumed to include production API capacity.

### 12.6 Accepted retention policy

The initial retention policy prioritizes dataset durability and the ability to improve historical extraction quality.

- Verified structured financial records, corrections, and provenance are retained indefinitely.
- Original receipt images are retained indefinitely during the initial data-building period. V1 must not delete them automatically.
- Raw and structured extraction outputs, extractor and prompt versions, validation results, and processing history are retained so receipts can be reprocessed and extraction changes can be evaluated.
- Sanitized statements are retained as authoritative monthly reconciliation evidence.
- Originals containing restricted identifiers follow a separately controlled lifecycle: encrypted restricted storage when preservation is required, or verified deletion after successful extraction and sanitization when it is not.
- Retention controls must be configurable so policies can change without rewriting ingestion or the canonical data model.
- Storage volume, cost, access patterns, and reprocessing value will be measured before any automatic lifecycle or archival rule is introduced.

### 12.7 Accepted access and authentication model

The initial application is a private, single-user system.

- Public registration and multi-user account management are out of scope.
- The owner's identity is explicitly allowlisted.
- Authentication uses a managed passwordless or trusted identity-provider flow. Financial OS must not implement or store custom passwords.
- After initial authentication, the iPhone maintains a persistent secure session so routine capture does not add login friction.
- A new device, revoked session, or defined session expiration requires reauthentication.
- The capture application is available through Wi-Fi or cellular connectivity from outside the home network.
- The server authenticates and authorizes every upload and private read request regardless of client state.
- Internet-facing endpoints use rate limiting, request-size limits, content validation, and privacy-safe audit records.
- Active sessions can be enumerated and revoked, including immediate revocation after device loss or suspected compromise.
- Authentication-provider details remain behind an application boundary so the provider can be replaced without changing the receipt or financial domain model.

### 12.8 Accepted extraction trust model

Processing progress and verification confidence are separate state dimensions. A record must not be described as human-confirmed merely because automated processing completed successfully.

The initial processing lifecycle is:

```text
uploaded → processing → extracted
                      ↘ failed
```

The initial verification lifecycle is:

```text
unreviewed → system_validated
          ↘ needs_review → human_verified
```

Rules:

- Capture acknowledgement does not wait for extraction or review.
- Schema, required-field, arithmetic, and plausibility validation run automatically.
- An internally consistent extraction that satisfies the configured policy may become `system_validated`.
- An extraction with missing material fields, arithmetic mismatch, ambiguity, or insufficient confidence becomes `needs_review`.
- Only an explicit human review may produce `human_verified` status.
- Extracted records remain queryable, but analytical results must expose or filter by verification level.
- Review and correction do not overwrite history. The system retains the original output, corrected value, actor, timestamp, and relevant processing versions.
- Numeric thresholds are configuration and evaluation decisions. They will be calibrated using representative receipt evidence and a fixed regression set rather than selected arbitrarily.

### 12.9 Accepted evidence-only historical backfill policy

Historical acquisition and go-forward capture are independent tracks.

#### Go-forward capture

- Daily physical-receipt capture begins as soon as the PWA is usable.
- Raw evidence is preserved even when extraction is incomplete or requires later review.
- Historical backfill work must not block or pause new daily acquisition.

#### Historical backfill

- Import available Capital One and Ally account activity from January 1, 2026 onward.
- Preserve every available authoritative monthly statement in scope.
- Import available Amazon, Costco, email receipt, pay-stub, bill, and physical-receipt history when source evidence exists.
- Never invent historical line items from a merchant name, transaction category, typical basket, model inference, or unsupported assumption.
- A transaction without item-level evidence may count toward financial coverage but must remain explicitly not itemized.
- All historical records retain source, import, processing, and verification provenance.

This policy keeps financial coverage and eligible purchase itemization coverage honest and independently measurable.

### 12.10 Accepted source automation priority

Automation follows user value, acquisition frequency, and delivery dependency rather than attempting to automate every source before daily capture begins.

#### Automatic in the day-one vertical slice

- iPhone receipt capture
- Authenticated upload and durable storage
- Receipt extraction, validation, and structured persistence

#### Automate in the first transaction-acquisition sprint

- Capital One Venture X transactions
- Ally personal checking transactions
- Use Plaid or another connector only after current coverage, permissions, pricing, historical access, and operational fit are verified.

#### Manual-first, then automate

- Monthly financial statements
- Amazon orders, shipments, returns, and refunds
- Costco purchase history
- Email receipts
- Employer pay stubs
- Utility bills

#### Manual exception unless volume changes

- Cash purchases

Every automated acquisition source must retain a documented manual import or capture fallback. Failure or unavailability of one provider must not prevent continued acquisition from other sources.

### 12.11 Accepted personal-first scope and rental boundary

The initial product analyzes personal finances only. Full rental-property management is deferred.

- Do not ingest the Ally rental checking account in the initial transaction-acquisition sprint.
- Do not model rental income, tenants, properties, units, or item-level rental spending in the initial release.
- Transactions on the shared Capital One card may be classified with a coarse `rental_property` context so they can be excluded from personal spending and behavior analysis.
- Lowe's and Home Depot transactions may be surfaced as rule-assisted rental candidates because they commonly represent maintenance items and tools. The rule is classification assistance, not an irreversible assumption.
- Rental-classified charges remain traceable in the transaction record but do not require receipt line-item analysis for the initial product.
- The canonical model preserves an explicit financial-context boundary so the later rental capability can be introduced without reinterpreting personal history.
- Existing rental spreadsheet workflows remain the operational system for rental activity until that future capability is approved.

### 12.12 Accepted initial deployment and Mac Mini transition

- Deploy the day-one PWA and backend to a managed cloud environment.
- Begin real daily receipt capture as soon as the day-one release gate passes.
- Treat the initial deployment as the first production acquisition system rather than disposable prototype code.
- Preserve exportable data, documented schemas, and tested backups so hosting components remain replaceable.
- Do not delay receipt acquisition for the Mac Mini or require an unnecessary temporary local deployment.
- Introduce the Mac Mini incrementally when it becomes available. Candidate responsibilities include a replicated or migrated financial data store, operational ledger, private analytics, and the network-isolated local language model.
- Cloud receipt ingestion may remain in place if it continues to provide the simplest reliable phone endpoint.
- Relocate backend responsibilities only when cost, reliability, privacy, performance, or architectural evidence justifies the change.
- Any migration requires verified data completeness, integrity checks appropriate to each artifact, rollback, and no material interruption to receipt capture.
- Stable client-facing APIs must prevent infrastructure relocation from requiring a rewrite of the PWA.

## 13. Preliminary first-release boundary

The broader first-release boundary is a personal financial acquisition and reconciliation system that:

- Imports transactions from the primary financial accounts through an approved automatic or repeatable method.
- Acquires historical records from January 1, 2026 onward.
- Preserves monthly statements as authoritative evidence.
- Captures physical receipts from an iPhone through an installable, mobile-first Progressive Web App with minimal interaction.
- Stores raw evidence durably according to a defined retention policy.
- Extracts structured receipt and line-item information.
- Matches purchase evidence to financial transactions.
- Prevents credit-card payments and other transfers from being double-counted.
- Keeps rental-related shared-card charges out of personal analysis through an explicit coarse classification.
- Exposes unmatched and review-required records.
- Reports financial coverage, itemization coverage, and reconciliation status.

This boundary is preliminary until the remaining automation, retention, integration, and first-milestone questions are resolved.

### 13.1 Approved day-one vertical slice

The first implementation milestone is approved when the user can:

1. Install the Progressive Web App on an iPhone home screen.
2. Open a camera-first capture experience.
3. Photograph and submit a receipt through an authenticated connection, using one image normally or multiple ordered images when necessary.
4. Receive an immediate upload acknowledgement.
5. Rely on the backend to preserve the original image and receipt metadata.
6. Automatically extract merchant, purchase date, totals, and line items.
7. Validate and persist the structured extraction result.
8. See whether processing succeeded, failed, or requires later review.
9. Retrieve the receipt record and extracted structured data through a minimal history or detail experience.

The vertical slice must include automated tests for its critical capture, upload, validation, and persistence behavior.

### 13.2 Deliberately excluded from day one

The following are committed roadmap capabilities but do not block daily receipt acquisition:

- Correction and review editing interface
- Plaid or other financial connector integration
- Receipt-to-transaction matching
- Statement reconciliation
- Amazon order ingestion
- Email receipt ingestion
- Advanced analytics and behavior analysis
- Conversational querying
- Native SwiftUI client
- Public registration and multi-user account administration

Deferring these capabilities from the day-one vertical slice does not remove them from product scope. Their planned sequence and exit criteria are maintained in `docs/product/roadmap.md`.

## 14. Explicitly deferred capabilities

The following capabilities are part of the longer-term vision but are not prerequisites for beginning data acquisition:

- Autonomous financial actions of any kind
- Advanced forecasting or investment modeling
- Goal-alignment and purchase-regret coaching
- A polished conversational interface
- Multi-user support
- Public hosting of personal financial data
- Full tax, accounting, or property-management functionality
- Complex distributed infrastructure without a demonstrated operational need

## 15. Product discovery closeout

The initial PRD discovery process is complete and this document is the approved product baseline.

The four closeout decisions are accepted:

1. Receipt capture is automated first; personal account acquisition follows; other evidence sources begin with manual fallbacks.
2. The initial product is personal-only, with a coarse boundary that excludes identifiable rental charges from personal analysis.
3. Day-one, 30-day, and post-matching success targets are measurable and evidence-based.
4. The first production acquisition system is cloud-hosted and begins daily capture immediately after its release gate; the Mac Mini is introduced incrementally without interrupting acquisition.

New implementation details discovered afterward will be handled through architecture, threat modeling, evaluation, ADRs, or sprint planning unless they materially change product intent.

The following topics no longer require sequential owner interviews before the PRD closes:

- Financial connector selection and historical coverage validation
- Complete restricted-field inventory and original-document handling
- Public-repository and private-runtime separation mechanics
- Numeric extraction and matching thresholds
- Remote-access implementation after Mac Mini deployment
- Operational ledger selection and relationship to the itemized evidence store

These topics will receive evidence-based recommendations in the architecture, threat model, evaluation plan, or implementation plan. The owner will be asked only when a choice materially changes product scope, acceptable risk, cost, or user experience.

Changes to this approved baseline require an explicit PRD amendment that records the reason, affected requirements, roadmap impact, and owner decision.

## 16. Related source documents

The following handoff documents contain the original product and architecture context:

- `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`
- `personal_ai_finance_codex_handoff.md`
- `docs/product/roadmap.md`
- `docs/governance/ai-development-operating-model.md`

They remain source material while this PRD consolidates decisions through product discovery.
