# {{PROJECT_NAME}} — AI Development Operating Model

**Status:** Proposed | Accepted  
**Owner:** {{OWNER}}  
**Operating lead:** {{OPERATING_LEAD_OR_ROLE}}  
**Created:** {{DATE}}  
**Last updated:** {{DATE}}

## 1. Purpose

This document defines how humans and AI-assisted development tools plan, implement, review, and operate {{PROJECT_NAME}}.

This policy is model- and tool-agnostic. Tool-specific instruction files and agent configurations are adapters. If an adapter conflicts with this document, this document governs until the owner approves a policy change.

## 2. Product and delivery mandate

**Product outcome:** {{ONE_PARAGRAPH_PRODUCT_OUTCOME}}

**Primary user:** {{PRIMARY_USER}}

**Delivery posture:** {{EXAMPLE: STARTUP SPEED WITH PRINCIPAL-LEVEL DECISION QUALITY}}

**Immediate release boundary:** {{SMALLEST USABLE RELEASE}}

**Non-negotiable constraints:**

- {{CONSTRAINT_1}}
- {{CONSTRAINT_2}}
- {{CONSTRAINT_3}}

The breadth of professional thinking must not expand the immediate feature scope without evidence that a requirement is necessary for user value, safe operation, or production viability.

## 3. Quality target

{{PROJECT_NAME}} is being developed as:

> {{ONE_SENTENCE_QUALITY_AND_DELIVERY_STANDARD}}

Claims of quality must be demonstrated through appropriate evidence such as:

- Product requirements and measurable acceptance criteria
- Architecture and decision records
- Threat model and data classification
- Automated tests and direct product demonstrations
- Reproducible build and deployment instructions
- Security, dependency, and secret controls
- Observability, failure handling, backup, and recovery evidence
- Synthetic or anonymized portfolio artifacts where applicable

Delete evidence categories that do not apply. Add project-specific evidence where necessary.

## 4. Authority and accountability

### 4.1 Owner

**Owner:** {{OWNER}}

The owner:

- Defines product intent, priority, acceptable risk, and cost boundaries.
- Approves material requirements and difficult-to-reverse tradeoffs.
- Authorizes external side effects, production access, and sensitive-data handling.
- Resolves legitimate tradeoffs that evidence alone cannot decide.

### 4.2 Operating lead

**Lead:** {{OPERATING_LEAD_OR_ROLE}}

The operating lead:

- Maintains the canonical PRD, roadmap, decision register, and acceptance criteria.
- Integrates product, engineering, security, data, and operational concerns.
- Protects the smallest valuable release from scope expansion.
- Converts assumptions into questions, research, prototypes, tests, or owner decisions.
- Prepares bounded execution packets.
- Synthesizes independent findings without hiding dissent.
- Verifies outcomes against artifacts, tests, measurements, and direct behavior.

### 4.3 Implementation lead

**Lead/tool:** {{IMPLEMENTATION_LEAD_OR_TOOL}}

The implementation lead:

- Reads the versioned execution packet and canonical project documents.
- Restates the outcome, constraints, non-goals, and acceptance evidence.
- Proposes the smallest safe implementation.
- Coordinates implementation and deterministic verification.
- Reports actual results, failures, changed assumptions, and residual risk.
- Does not mark work complete without the required evidence.

## 5. Integrated decision lenses

Apply the relevant questions to every meaningful decision.

### Product and UX

- What user outcome changes after this ships?
- What is required now versus useful later?
- What is the smallest complete vertical slice?
- What would prevent adoption or continued use?
- How will value and quality be measured?

### Engineering and architecture

- What invariants and contracts must remain stable?
- What is reversible, and what requires a decision record?
- How does this affect integrity, migrations, idempotency, and recovery?
- Is the design simple, testable, comprehensible, and replaceable where necessary?

### Security and privacy

- What assets, identities, trust boundaries, threats, and impacts exist?
- What is the smallest effective, testable control?
- Can access be revoked and failures contained and investigated?
- Does the control preserve the primary user workflow?

### DevOps and reliability

- How is this built, configured, deployed, observed, rolled back, backed up, and restored?
- What happens when a dependency fails?
- Are logs actionable and safe?
- What manual fallback preserves the outcome?

### Data and AI quality

- What is authoritative evidence versus normalization, calculation, inference, or correction?
- Can every result expose provenance and trust state?
- What evaluation detects quality changes?
- Can a provider or model be replaced without changing core domain meaning?

Add or remove lenses to match the project.

## 6. Independent reviewers

Use {{REVIEWER_COUNT}} independent reviewers for the formal plan and release gates.

Each reviewer receives the same immutable evidence packet, works without seeing other reviewers' conclusions, performs a complete go/no-go assessment, and emphasizes a distinct charter.

### Reviewer A — {{CHARTER_A_NAME}}

**Primary posture:** {{CHARTER_A_POSTURE}}

**Primary concerns:**

- {{CHARTER_A_CONCERN_1}}
- {{CHARTER_A_CONCERN_2}}
- {{CHARTER_A_CONCERN_3}}

### Reviewer B — {{CHARTER_B_NAME}}

**Primary posture:** {{CHARTER_B_POSTURE}}

**Primary concerns:**

- {{CHARTER_B_CONCERN_1}}
- {{CHARTER_B_CONCERN_2}}
- {{CHARTER_B_CONCERN_3}}

### Reviewer C — {{CHARTER_C_NAME_OR_DELETE_SECTION}}

**Primary posture:** {{CHARTER_C_POSTURE}}

**Primary concerns:**

- {{CHARTER_C_CONCERN_1}}
- {{CHARTER_C_CONCERN_2}}
- {{CHARTER_C_CONCERN_3}}

Every reviewer evaluates the complete plan. A specialty does not permit a reviewer to ignore a concern that makes the product unsafe, incoherent, unbuildable, or unverifiable.

## 7. Independence protocol

1. Freeze the evidence packet by commit or immutable artifact version.
2. Give every reviewer the same artifact manifest, scope, constraints, and response template.
3. Do not provide other reviewers' findings during the independent pass.
4. Restrict reviewers to read-only tools unless a bounded experiment is authorized.
5. Require assumptions, unknowns, evidence, findings, residual risks, and a verdict.
6. Collect all reviews before synthesis.
7. Preserve disagreements and minority findings.
8. Invalidate and rerun affected sign-offs after material artifact changes.

## 8. Evidence standard

A material recommendation requires at least one of:

- An owner-approved requirement
- A cited authoritative standard or primary vendor source
- A repository artifact, executable test, or direct observation
- A measurement, benchmark, prototype, or controlled experiment
- A reasoned inference with explicit premises and uncertainty

Unsupported appeals to “best practice,” agent consensus, model prestige, framework popularity, or imagined scale are insufficient.

Unknowns remain unknown. Material assumptions require an owner, validation method, and decision deadline.

## 9. Verdict and sign-off

Allowed verdicts:

- **Approve:** No unresolved blocking or high-severity condition.
- **Approve with conditions:** Conditions are explicit, owned, testable, and non-blocking for this gate.
- **Reject:** An unresolved issue makes the plan unsafe, incoherent, untestable, or unlikely to achieve the outcome.

Formal sign-off requires {{SIGN_OFF_RULE}}.

A rejection blocks the gate until the issue is resolved, disproved, or explicitly accepted by the owner as a documented risk.

AI sign-off is an evidence-backed review record, not a transfer of accountability from the human owner.

## 10. Quality gates

### Gate A — Product and implementation readiness

**When:** {{GATE_A_TIMING}}

**Evidence:** {{GATE_A_REQUIRED_ARTIFACTS}}

**Review:** {{GATE_A_REVIEWERS}}

### Gate B — Iteration readiness

**When:** Before a sprint, milestone, or vertical slice.

**Evidence:** Outcome, non-goals, acceptance criteria, dependencies, risks, and fallback.

**Review:** Implementation lead plus risk-appropriate specialists.

### Gate C — Change readiness

**When:** Before merging or integrating a meaningful change.

**Evidence:** Deterministic checks, targeted review, documentation, and demonstrated behavior.

### Gate D — Release readiness

**When:** Before production deployment or processing a new sensitive data class.

**Evidence:** Product outcome, access controls, observable failure handling, recovery, and residual risks.

### Gate E — Strategic audit

**When:** {{STRATEGIC_AUDIT_TIMING}}

**Model/reviewer:** {{STRONGEST_REASONING_MODEL_OR_REVIEWER}}

**Purpose:** Challenge system-wide assumptions. This gate supplements rather than replaces tests and prior reviews.

## 11. Orchestration and capacity strategy

**Constrained resource:** {{CONSTRAINED_TOOL_OR_MODEL_AND_HOW_TO_USE_IT}}

**High-throughput resource:** {{PRIMARY_IMPLEMENTATION_ENVIRONMENT_AND_CAPACITY}}

**Default implementation model:** {{DEFAULT_MODEL}}

**Strategic review model:** {{STRATEGIC_MODEL}}

Rules:

- Use the constrained resource for high-value supervision, decisions, synthesis, and acceptance work.
- Use the high-throughput implementation environment for routine planning, coding, testing, and bounded parallel work.
- Spawn independent agents when work is separable, ownership is clear, and parallelism shortens delivery.
- Use isolated workspaces or worktrees for concurrent edits.
- Keep shared schemas, contracts, and migration chains under one owner.
- Avoid communicative agent teams when isolation and report-back are the desired behavior.
- Track usage to diagnose inefficiency, not to create an arbitrary cap unless the owner defines one.
- Replace repeatable reasoning with tests, scripts, templates, hooks, and skills.
- Escalate models based on risk or unresolved complexity rather than prestige.

## 12. Delivery loop

1. **Frame:** Confirm outcome, non-goals, acceptance evidence, and owner decisions.
2. **Packet:** Create a versioned execution packet.
3. **Plan:** The implementation lead proposes the smallest safe approach.
4. **Challenge:** Run risk-appropriate independent review.
5. **Implement:** Use bounded work units and parallelism where safe.
6. **Verify:** Run deterministic checks and demonstrate actual behavior.
7. **Review:** Require evidence-backed findings.
8. **Decide:** Dispose findings transparently and escalate owner decisions.
9. **Ship:** Deploy with proportional health, fallback, and rollback.
10. **Learn:** Update canonical documents from observed results.

## 13. Pace protections

- Scale review intensity with risk and reversibility.
- Do not require the full reviewer panel for every commit.
- Do not expand the immediate release unless a requirement is necessary for value, safe use, or operability.
- Put advisory improvements in the backlog rather than blocking shipment.
- Earn architecture through observed variation, risk, or load.
- Prefer a working vertical slice with controlled limitations over a comprehensive untested platform.

## 14. Tool adapters

After approval, implement this policy through the tools the project actually uses:

- Root contributor instructions
- `AGENTS.md`, `CLAUDE.md`, or equivalent adapters
- Project-scoped reviewer definitions
- Execution and review templates
- Session, planning, review, and release procedures
- Deterministic CI and evidence reports

Tool adapters must point to this policy and may not silently weaken it.

## 15. Owner approval

**Decision:** Pending | Approved | Approved with changes  
**Owner:** {{OWNER}}  
**Date:** {{DATE}}  
**Notes:** {{APPROVAL_NOTES}}
