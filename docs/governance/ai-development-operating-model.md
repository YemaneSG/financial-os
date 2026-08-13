# Financial OS — AI Development Operating Model

**Status:** Accepted  
**Owner:** Yemane  
**Operating lead:** Codex  
**Created:** August 12, 2026  
**Last updated:** August 12, 2026

## 1. Purpose

This document defines how humans and AI-assisted development tools will plan, implement, review, and operate Financial OS.

The operating model is tool- and model-agnostic. Product authority, reviewer charters, evidence requirements, and quality gates live here. Tool-specific files such as `AGENTS.md`, `CLAUDE.md`, agent definitions, skills, commands, and hooks are adapters that implement this policy; they are not the canonical policy.

## 2. Owner mandate

Financial OS must combine startup speed with principal-level decision quality.

The owner expects the operating lead and implementation system to reason simultaneously through these perspectives:

- **World-class product leadership:** identify the user outcome, find the smallest valuable release, maintain product coherence, make tradeoffs explicit, and move from idea to production quickly.
- **Principal/staff software engineering:** connect decisions across the client, API, data model, ingestion pipelines, security boundaries, operations, and future intelligence layer; preserve evolvability without premature abstraction.
- **Security leadership:** protect restricted identifiers, credentials, financial data, and production access through risk-proportionate controls that enable delivery rather than creating ceremonial delay.
- **DevOps and reliability leadership:** make every release deployable, observable, reversible, recoverable, and affordable using the smallest adequate operational footprint.
- **Data and AI product leadership:** treat provenance, correction history, reconciliation, deterministic calculations, extraction evaluation, and provider replaceability as core product capabilities.

The day-one product remains deliberately small: an installable iPhone PWA and backend that capture receipts and produce durable structured data. The breadth of professional thinking must not expand the day-one feature scope unless evidence proves a requirement is necessary for safe use.

## 3. What level this project is targeting

Financial OS is being developed as:

> A production-minded, single-user financial data product built with principal-caliber engineering judgment, startup-caliber delivery speed, and security appropriate to sensitive personal and financial data.

It is also intended to become a credible public portfolio case study for senior software-engineering and technical product-management roles. The portfolio claim must be demonstrated through artifacts and evidence rather than visual polish or architectural complexity.

Evidence should include:

- A coherent PRD and outcome roadmap
- Explicit domain rules and Architecture Decision Records
- A threat model and data-classification policy
- Traceable requirements and acceptance tests
- Reproducible builds and deployments
- CI, dependency, secret, and security controls
- Measured extraction and data-quality performance
- Operational telemetry, failure handling, backup, and restoration evidence
- A synthetic demonstration dataset that exposes no private user data
- Clear tradeoff explanations suitable for design and product interviews

## 4. Authority and accountability

### 4.1 Owner

Yemane is the product owner and final human authority.

The owner:

- Defines product intent, acceptable risk, cost boundaries, and priority.
- Approves material requirements and irreversible tradeoffs.
- Resolves disagreements where evidence supports multiple legitimate choices.
- Authorizes external accounts, production deployments, connector access, and handling of real financial data.

### 4.2 Operating lead

Codex serves as the product and technical-program operating lead during discovery and cross-system supervision.

The operating lead:

- Maintains the canonical PRD, roadmap, decision register, acceptance criteria, and implementation brief.
- Integrates product, engineering, security, data, and operational concerns into one coherent plan.
- Protects the smallest valuable release from scope expansion.
- Identifies assumptions and converts them into questions, research, prototypes, tests, or explicit owner decisions.
- Prepares bounded execution packets for the implementation lead.
- Evaluates independent review findings skeptically and records their disposition.
- Verifies claimed outcomes against artifacts, tests, measurements, and observable product behavior.
- Escalates genuine product authority decisions to the owner rather than silently deciding them.

The operating lead is not permitted to treat an AI recommendation, including its own, as evidence merely because it sounds authoritative.

### 4.3 Implementation lead

Claude Code will serve as the primary implementation lead when access is provided.

The implementation lead must mirror the integrated product and engineering posture defined here. It is responsible for:

- Reading the canonical project packet before planning work.
- Restating the sprint outcome, constraints, non-goals, and acceptance evidence.
- Producing the smallest implementation plan that satisfies the approved outcome.
- Coordinating implementation and deterministic verification.
- Preserving repository and data safety.
- Reporting actual results, failures, residual risks, and changed assumptions without embellishment.
- Refusing to mark a milestone complete without its required evidence.

The implementation lead may coordinate specialized agents, but it remains responsible for synthesis and cannot outsource judgment to a majority vote.

## 5. Integrated operating posture

The operating and implementation leads apply the following questions to every meaningful decision.

### Product

- What user outcome changes after this work ships?
- Is this required now, or merely useful later?
- What is the smallest complete vertical slice?
- How will adoption, quality, or coverage be measured?
- What would cause the user to stop using the product?

### Engineering and architecture

- What contracts and domain invariants must remain stable?
- Which future change is likely enough to justify an interface today?
- What is reversible, and what deserves an ADR?
- How does this change affect data integrity, migrations, idempotency, and failure recovery?
- Can the implementation be understood and operated by another competent engineer?

### Security and privacy

- What assets, identities, and trust boundaries are involved?
- What is the credible threat and likely impact?
- What is the smallest effective control?
- Does the control reduce risk without breaking the core workflow?
- Can failure be detected, contained, revoked, and investigated?

### DevOps and reliability

- How is the change built, configured, deployed, observed, rolled back, backed up, and restored?
- What fails when a dependency is unavailable?
- Are logs actionable without exposing private data?
- Does the operating cost match current scale?
- What manual fallback preserves the user outcome?

### Data and AI quality

- What is the authoritative source?
- What is raw evidence, normalized fact, deterministic calculation, model inference, or human correction?
- Can every result identify its provenance and verification state?
- What fixed evaluation or regression evidence detects quality changes?
- Can the provider or model be replaced without rewriting domain logic?

## 6. Independent review system

Three independent reviewers will assess the completed product plan and implementation plan before implementation begins.

They receive the same versioned evidence packet and must not receive another reviewer's conclusions during their first pass. They do not collaborate, negotiate, or inherit assumptions from one another. Each reviewer performs a complete go/no-go assessment while emphasizing its primary charter.

### Reviewer A — Product and delivery

**Primary posture:** World-class startup product leader and technically fluent delivery executive.

**Primary questions:**

- Is the user problem and outcome precise?
- Is the scope the smallest version that produces real learning and value?
- Are priorities, non-goals, dependencies, and success measures coherent?
- Does the roadmap preserve important future capabilities without blocking the first release?
- Can this plan plausibly reach a usable product at the stated speed?
- Are adoption friction, failure recovery, and behavior-change risks addressed?

### Reviewer B — Principal architecture and engineering

**Primary posture:** Principal/staff software engineer and system/data architect.

**Primary questions:**

- Do the system boundaries, domain model, data contracts, and state machines support the accepted product?
- Are financial semantics, provenance, idempotency, reconciliation, and migrations handled correctly?
- Is the design appropriately simple, modular, testable, and provider-independent?
- Are failure modes, concurrency, duplicate handling, and future data sources represented without speculative infrastructure?
- Is the implementation plan executable in safe vertical slices?

### Reviewer C — Security, production, and reliability

**Primary posture:** Senior security engineer, DevSecOps lead, and production SRE.

**Primary questions:**

- Are data classes, threats, identities, secrets, and trust boundaries explicit?
- Are the controls proportional, testable, and compatible with the capture experience?
- Can the system be securely deployed, observed, revoked, rolled back, backed up, and restored?
- Are dependencies, supply chain, logging, incident response, and cost failure modes addressed?
- Does any convenience decision create an unacceptable or unacknowledged risk?

### Common obligation

Every reviewer must evaluate the full plan, not only its specialty. A reviewer cannot sign off on a product it believes is unsafe, unbuildable, incoherent, or unverifiable merely because the problem falls outside its primary charter.

## 7. Independence protocol

For a formal three-reviewer gate:

1. Freeze and identify the evidence packet by commit or immutable artifact version.
2. Give each reviewer the same artifact list, scope, user constraints, and review template.
3. Do not include the operating lead's preferred solution beyond decisions already accepted in canonical documents.
4. Do not expose reviewer outputs to the other reviewers during the independent pass.
5. Restrict reviewers to read-only repository and diagnostic capabilities unless a bounded experiment is explicitly authorized.
6. Require each reviewer to enumerate assumptions, unknowns, evidence, findings, and verdict.
7. Collect all reviews before synthesis begins.
8. Preserve disagreements and minority findings in the synthesis; do not collapse them into a majority opinion.
9. Re-run an affected review when the reviewed artifacts change materially.

## 8. Evidence standard

Every material recommendation or finding must be supported by at least one of:

- An explicit owner-approved requirement
- A cited authoritative standard or primary vendor document
- A repository artifact, executable test, or direct observation
- A measurement, benchmark, prototype, or controlled experiment
- A clearly reasoned inference whose premises and uncertainty are stated

The following are not sufficient by themselves:

- “Best practice” without the risk or outcome it addresses
- Model confidence or consensus among agents
- A framework's popularity
- An unsupported prediction about future scale
- A reviewer title or model tier

Unknowns must be labeled as unknowns. Assumptions must have an owner, validation method, and decision deadline if they could affect scope or architecture.

## 9. Finding and verdict format

Each independent review must contain:

1. Reviewer charter and model or tool used
2. Exact artifacts and versions reviewed
3. Independent summary of the proposed product and implementation
4. Assumptions and unresolved questions
5. Strengths supported by evidence
6. Findings ranked as blocking, high, medium, or advisory
7. Required changes and how their completion can be verified
8. Explicit non-findings where a commonly expected concern was evaluated and dismissed
9. Residual risks
10. Verdict

Allowed verdicts:

- **Approve:** No unresolved blocking or high-severity condition.
- **Approve with conditions:** Conditions are explicit, owned, testable, and non-blocking for the stated gate.
- **Reject:** At least one unresolved issue makes the plan unsafe, incoherent, untestable, or unlikely to achieve the approved outcome.

Formal sign-off requires all three reviewers to issue `Approve` or `Approve with conditions`. A `Reject` blocks the gate until the finding is resolved, explicitly accepted by the owner as a documented risk, or disproved with evidence.

## 10. Synthesis and skepticism protocol

After the independent pass, the operating or implementation lead creates a finding matrix with one row per distinct claim.

For every recommendation, the lead records:

- The claim
- Reviewer and severity
- Supporting evidence
- Counterevidence or conflicting findings
- Impact on user value, scope, delivery time, security, and cost
- Disposition: accept, reject, defer, investigate, or escalate to owner
- Rationale and verification method

The lead must actively test strong-sounding recommendations. It should ask:

- What concrete failure does this prevent?
- Is the failure plausible at current scale?
- Can a simpler control address it?
- Does this recommendation contradict an approved product constraint?
- What evidence would falsify it?
- Is the reviewer solving a different problem from the one in the PRD?

Sign-off is not a vote. The goal is to surface independent evidence and make a reasoned decision while preserving accountability.

## 11. Quality gates

### Gate A — Product and implementation readiness

**When:** After PRD, architecture, threat model, and implementation plan are ready; before Sprint 0 or Sprint 1 implementation materially begins.

**Reviewers:** All three independent reviewers.

**Required outcome:** All reviewers sign off under the verdict rules above, and the owner approves any material product or risk tradeoff.

### Gate B — Sprint readiness

**When:** Before each sprint.

**Reviewers:** Implementation lead plus the one specialist whose domain is materially affected. Use all three only for cross-cutting or high-risk work.

**Required outcome:** Outcome, non-goals, acceptance evidence, migration impact, security considerations, and rollback or fallback are explicit.

### Gate C — Change readiness

**When:** Before merging a meaningful vertical slice.

**Reviewers:** Deterministic CI plus targeted human or AI review based on changed risk.

**Required outcome:** Tests pass; secrets and private data are absent; relevant requirements are demonstrated; documentation and operational changes are complete.

### Gate D — Release readiness

**When:** Before deploying a milestone to production or processing a new class of real financial data.

**Reviewers:** Product, engineering, and security/production coverage. Full independent review is required for the first production release and material trust-boundary changes.

**Required outcome:** The product outcome works, failure handling is observable, access is controlled, recovery is tested proportionally, and residual risks are recorded.

### Gate E — Opus-level strategic audit

**When:** After sufficient implementation evidence exists, before a major architectural commitment, and before the mature public portfolio or long-term production milestone.

**Purpose:** Challenge system-wide assumptions using the strongest available reasoning model. This is not a substitute for tests or earlier review.

## 12. Throughput-optimized Claude Code orchestration

Claude Code through Vertex AI is the primary high-throughput implementation environment for this project. Its available project budget is not a material delivery constraint. The orchestration objective is therefore to maximize safe shipping speed and product quality, while avoiding coordination patterns that create rework or reduce clarity.

Codex usage through the owner's ChatGPT plan is comparatively constrained. Codex capacity should be reserved for the product-lead and supervisory work where continuity with the owner conversation and cross-project judgment add the most value.

### 12.1 Default execution pattern

- Use a Sonnet implementation-lead session for routine planning, coding, integration, and verification.
- Give it a compact, versioned execution packet rather than replaying conversational history.
- Use deterministic tools for formatting, tests, schemas, migrations, security scans, and deployment checks.
- Spawn independent Sonnet agents whenever work can be bounded, parallelized safely, and verified independently.
- Use up to the authorized concurrent-agent limit when parallel work will shorten delivery without creating file, schema, or decision conflicts.
- End agents when their task is complete and begin fresh sessions for unrelated work so stale context does not degrade results.

### 12.2 Three-agent formal review

For Gate A and other explicitly designated gates:

- Launch exactly three project-scoped, read-only agents matching the reviewer charters.
- Use Sonnet for the initial independent passes unless a specific review demonstrably requires Opus.
- Give each agent the same concise artifact manifest and structured output contract.
- Prevent cross-reviewer communication during the independent pass.
- Set bounded turns and require a final verdict rather than open-ended exploration.
- Have the lead synthesize only after all three results are available.

Custom subagents are preferred over a communicative agent team for the independent review pass because the required behavior is isolation and report-back, not collaboration. Avoid agent teams unless implementation genuinely requires direct cross-agent coordination; shared communication is not an advantage for independent analysis.

### 12.3 Parallel implementation

Parallel implementation is encouraged when work units are independently testable and have clear file or module ownership.

- Use isolated worktrees when agents may edit concurrently.
- Do not assign multiple agents to the same files or migration chain.
- Integrate one bounded change at a time with tests at each boundary.
- Keep shared schema or contract changes under one owner.
- Prefer a single lead for sequential debugging, refactoring, or tightly coupled changes.
- Use independent implementation agents for separate client, API, infrastructure, test, documentation, or research workstreams when their inputs and outputs can be specified in advance.

### 12.4 Opus usage

Reserve Opus for:

- Final challenge of the product and architecture plan when requested
- Irreversible or high-risk architectural decisions
- Security findings with ambiguous system-wide consequences
- Complex failures that remain unresolved after evidence-based Sonnet investigation
- Major release or portfolio audit

Do not use Opus merely to repeat a review that Sonnet and deterministic evidence already resolved.

### 12.5 Codex usage

Use Codex primarily for:

- Product discovery and owner conversation
- Canonical PRD, roadmap, governance, and decision synthesis
- Preparing concise Claude Code execution packets
- Independent challenge of material plans or disputed findings
- Acceptance verification and cross-sprint coherence

Avoid duplicating routine implementation already assigned to Claude Code. Summaries should point to canonical repository artifacts rather than paste long histories into both systems.

### 12.6 Capacity and efficiency controls

- Do not impose an artificial Claude Code token or agent budget on this project when additional independent work will materially improve delivery speed or quality.
- Track model and agent usage as operational telemetry so inefficient prompts, repeated failures, or unbounded sessions can be diagnosed; usage tracking is not a shipping cap.
- Record repeatable activities and replace repeated reasoning with scripts, tests, templates, hooks, or skills when doing so makes future work faster and more reliable.
- Keep always-loaded instruction files concise; place detailed procedures in referenced governance documents or skills.
- Use Sonnet freely for implementation and independent agent work. Escalate to Opus when the decision risk or unresolved complexity warrants it, not merely for prestige.
- Optimize the constrained Codex allocation by avoiding implementation duplication, long unstructured transcripts, and work Claude Code can complete from a bounded execution packet.

## 13. AI-driven delivery loop

For each vertical slice:

1. **Frame:** Codex and the owner confirm outcome, non-goals, acceptance evidence, and unresolved authority decisions.
2. **Packet:** Codex creates a versioned execution packet referencing canonical documents and relevant source files.
3. **Plan:** Claude Code restates constraints and proposes the smallest safe implementation.
4. **Challenge:** The appropriate reviewer checks the plan when risk warrants it.
5. **Implement:** Sonnet leads; parallel agents are used only for independent work.
6. **Verify:** Deterministic checks run first. Product behavior is demonstrated against acceptance criteria.
7. **Review:** Findings cite evidence; high-risk changes receive specialist review.
8. **Decide:** The lead disposes findings transparently; the owner resolves material product or risk tradeoffs.
9. **Ship:** Deploy with observable health, fallback, and rollback appropriate to the slice.
10. **Learn:** Update the PRD, roadmap, ADRs, open items, evaluations, and next-sprint priorities from actual evidence.

## 14. Pace protections

To prevent “world-class” from becoming slow or ceremonial:

- Review intensity scales with reversibility and risk.
- The full three-reviewer gate is not required for every commit.
- Day-one scope does not expand unless a missing control is necessary to prevent material harm or make the slice operable.
- Advisory findings enter the backlog instead of blocking shipment.
- Architecture is earned by real variation, load, or risk—not imagined future scale.
- Managed services and open-source components are both acceptable; selection follows evidence on speed, cost, security, and portability.
- A working vertical slice with known, controlled limitations is preferred to a comprehensive untested platform.

## 15. Tool-specific implementation adapters

After this operating model is approved, the repository should implement it through:

- A concise model-agnostic root contributor file and `AGENTS.md`
- A `CLAUDE.md` adapter that points to the same canonical documents
- Three project-scoped Claude reviewer definitions with read-only tool policies
- Structured review and sign-off templates
- Session-start, sprint-planning, review, and release-check procedures
- CI quality gates and privacy-safe evidence reports
- An implementation-handoff template that records artifact versions and acceptance criteria

No tool-specific adapter may silently weaken or override this canonical operating model.

## 16. Current state

- PRD discovery is intentionally paused.
- The evidence-only historical backfill decision has been recorded.
- This operating model is owner-approved, including the corrected capacity strategy.
- No implementation or Claude Code agent configuration has begun.
