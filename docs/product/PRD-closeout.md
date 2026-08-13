# Financial OS — Initial PRD Closeout

**Date:** August 12, 2026  
**Decision:** Approved product baseline  
**Owner:** Yemane

## Product statement

> Account for every dollar and itemize every purchase wherever item-level evidence exists.

## Immediate objective

Begin acquiring durable, analysis-ready personal receipt data through an installable iPhone PWA and production cloud backend. Optimize the first release for a reliable five-to-ten-second capture experience and preserve evidence for future behavior analysis.

## Approved day-one outcome

The user can install the PWA, photograph a single-image or multi-image receipt, upload it through a persistent authenticated session, receive acknowledgement, and later retrieve the original evidence and structured extraction result with an explicit processing and verification state.

## Accepted scope boundaries

- Personal finance only in the initial product
- Coarse classification to exclude identifiable rental-related shared-card charges from personal analysis
- No full rental account, income, property, unit, or itemization capability yet
- No correction interface, transaction connector, matching, Amazon/email ingestion, analytics, chat, or SwiftUI requirement for day one
- These deferred capabilities remain sequenced in the approved outcome roadmap

## Acquisition order

1. Automatic receipt capture, upload, extraction, validation, and storage
2. Capital One Venture X and Ally personal checking transaction acquisition
3. Manual-first statements, Amazon, Costco, email receipts, pay stubs, and utility bills, followed by automation
4. Manual cash exceptions unless volume changes

Every automated source retains a documented fallback.

## Trust and retention

- Processing state and verification state remain separate.
- Capture never waits for human review.
- Raw evidence, structured data, correction history, extraction versions, and provenance are retained.
- V1 does not automatically delete receipt images.
- Restricted identifiers and credentials follow a separate sanitization and controlled-storage lifecycle.
- Historical line items are created only from actual evidence, never inferred from merchant names or typical purchases.

## Initial success targets

- Zero loss of acknowledged uploads
- Explicit terminal or review status for every upload
- At least 95% of release-test receipts processed within two minutes
- Five-to-ten-second normal capture workflow, excluding backend processing
- At least 95% processing success during the first 30 days
- At least 90% of receipt totals reconciled or correctly flagged for review
- Verified 50-receipt regression set before field-accuracy targets are finalized
- Later: at least 99% personal financial coverage, 100% available statement reconciliation, and itemization coverage progressing from 80% toward 95%

## Deployment decision

- Ship the first production acquisition system in a managed cloud environment.
- Begin daily capture immediately after the release gate passes.
- Preserve stable APIs, exportable data, backups, and provider replaceability.
- Introduce the Mac Mini incrementally for the ledger, replicated or migrated data, private analytics, and local language model.
- Do not interrupt receipt acquisition or rewrite the PWA merely to relocate backend components.

## Operating model

- Codex is the product and technical-program operating lead.
- Claude Code through Vertex AI is the high-throughput implementation lead.
- Sonnet agents are used aggressively for bounded independent implementation and review work.
- Three independent reviewers assess product/delivery, architecture/engineering, and security/production before material implementation begins.
- Recommendations require evidence; agent consensus and appeals to “best practice” are insufficient.
- Yemane remains the final product and risk authority.

## What happens next

PRD discovery is closed. The next work is not another product-question sequence. It is to create:

1. A consolidated requirements traceability matrix
2. System and data architecture
3. Threat model and security control baseline
4. Day-one user flow and minimal UX specification
5. Technology and deployment recommendation with evidence
6. Sprint 0 and Sprint 1 implementation plan and execution packet
7. Three independent plan reviews and documented sign-off

Technical recommendations will be presented with defaults and evidence. Owner input will be requested only for decisions that materially change product scope, risk tolerance, cost, or user experience.
