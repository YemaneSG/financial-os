# AGENTS.md — Financial OS

> Model-agnostic contributor guide for all AI agents, automated tools, and human contributors.  
> Tool-specific adapters (`CLAUDE.md`, agent definitions, skills, hooks) implement this policy and may not override it.  
> Canonical policy lives in `docs/governance/ai-development-operating-model.md`.

---

## 1. Canonical document authority

**P-03 resolution — precedence order (highest to lowest):**

| Tier | Documents | Status |
|---|---|---|
| 1 — Security floor | `docs/security/control-baseline.md` MUST controls | Release blocking; may never be silently waived |
| 2 — Product contract | `docs/product/PRD.md`, `docs/product/roadmap.md`, `docs/product/open-items-and-decisions.md` | Authoritative scope, outcomes, accepted decisions, and open items |
| 3 — Architecture contract | `docs/architecture/system-architecture.md`, `docs/architecture/data-architecture.md`, `docs/architecture/technology-recommendation.md` | Authoritative design and data model |
| 4 — Implementation contract | The current owner-approved packet in `docs/implementation/execution-packets/`, plus `docs/architecture/implementation-contracts.md` | Authoritative for the bounded implementation slice |
| 5 — Governance | `docs/governance/ai-development-operating-model.md` | Authoritative for process and roles |
| 6 — Supporting context | `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`, `personal_ai_finance_codex_handoff.md` | Informational only; superseded by Tiers 1–5 on any conflict |

**Plaid, Actual Budget, rental day-one scope, SwiftUI, and multi-user features are explicitly rejected from Wave 1** — Section 6 of `docs/reviews/gate-a/synthesis-and-disposition.md`. No tier-6 document overrides this.

If a conflict exists between any two documents, **stop and report the conflict** before implementing. Do not silently resolve it in favor of either side.

---

## 2. Day-one product identity

Financial OS is a **private, single-owner, installable iPhone PWA** that captures receipt photos and produces durable structured financial data. The backend is a **portable modular monolith** on managed GCP.

The smallest complete day-one vertical slice:

> Install PWA → authenticate → photograph receipt → upload → receive durable acknowledgement → retrieve structured data or explicit failure state.

Nothing outside this flow is authorized for Wave 1 implementation.

---

## 3. Agent roles and authority

### 3.1 Owner (Yemane)

Final human authority. Approves material requirements, irreversible tradeoffs, production deployments, and real financial data handling. All other roles are delegated from the owner.

### 3.2 Operating lead (Codex)

Maintains canonical PRD, roadmap, and decision register. Creates bounded execution packets. Synthesizes independent review findings. Escalates genuine product-authority questions to the owner rather than deciding them unilaterally.

### 3.3 Supervisor / integration lead (Claude Code)

Reads the full canonical packet before planning. States the outcome, constraints, non-goals, and acceptance evidence before writing a line of code. Owns shared contracts, migrations, and root configuration. Coordinates workstream agents without outsourcing judgment to them.

### 3.4 Workstream implementation agents

Use the roles, file boundaries, and workstream labels frozen in the current owner-approved execution packet. The Wave 1 baseline was:

| Workstream | File scope | Boundary |
|---|---|---|
| A — Mobile PWA | `apps/web/` and web tests | Contract consumer; no server or infra changes |
| B — Receipt service | `apps/api/`, `src/financial_os/`, `tests/`, `alembic/` | Contract consumer; proposes contract deltas to supervisor |
| C — Platform / verification | `infra/`, `.github/`, scripts, synthetic E2E harness | Contract consumer; no domain or API implementation |

Agents **submit proposed contract deltas** to the supervisor for approval; they do not modify `contracts/`, root config, or migrations without supervisor integration. A later approved packet may reassign the workstream labels and file scopes while preserving this integration rule.

### 3.5 Review agents (Gate A / B / C)

Operate in **read-only mode**. Receive the same versioned artifact list; do not receive another reviewer's conclusions during the independent pass. Produce a finding report in the format specified in `docs/governance/ai-development-operating-model.md` §9. Allowed verdicts: `Approve`, `Approve with conditions`, `Reject`.

---

## 4. Before starting any work

Every agent must, in order:

1. Read the execution packet assigned to it (listed in §3.4 or the supervisor's briefing).
2. Read the tier-1 and tier-2 canonical documents listed in §1.
3. Restate the sprint outcome, non-goals, and acceptance evidence in its own words before planning.
4. Identify any conflict between the assigned packet and a canonical document; stop and report rather than resolving silently.
5. Propose the smallest implementation plan that satisfies the approved outcome.

---

## 5. What agents must never do

- Expand beyond the current owner-approved execution packet. Unless that packet explicitly authorizes an item, do not add Plaid, Actual Budget, bank connectors, Amazon/email ingestion, correction UI, transaction matching, analytics, SwiftUI, Android, multi-user, rental itemization, event streaming, Kubernetes, or Redis.
- Emit real GCP project IDs, Firebase project identifiers, service-account email addresses, or real production resource names in any file, log, screenshot, or CI artifact intended for the public repository.
- Commit secrets, credentials, signed URLs, auth tokens, or database passwords to source control.
- Commit real receipt images, extracted financial content from real receipts, owner personal data (email, address, SSN, card numbers), or raw model output from private evidence.
- Silently weaken `REL-001` (zero acknowledged receipt loss), owner-only authorization, private storage, or the no-tools AI boundary.
- Use binary floating-point types for money. All currency totals use integer minor units; quantities and high-precision unit prices use `NUMERIC`/`Decimal`.
- Mark a milestone complete without the required acceptance evidence.
- Run destructive cloud commands (delete buckets, drop databases, revoke IAM in production) without explicit owner authorization in the current session.
- Change a frozen Wave 1 contract without supervisor approval and affected-agent notification.
- Introduce microservices, event buses, or service mesh patterns absent from the approved architecture.

---

## 6. Contract freeze and delta protocol

The following files are frozen after Wave 1 contract publication:

- `contracts/openapi.yaml`
- `contracts/extraction-result.schema.json`
- `docs/architecture/implementation-contracts.md`
- `alembic/versions/` (existing migrations)
- `pyproject.toml` (dependency versions)

**Delta process:**
1. Workstream agent identifies a required change and files a brief proposal (one-paragraph description, affected routes/tables, backward-compatibility analysis).
2. Supervisor reviews, approves, and makes the change as integration owner.
3. Supervisor notifies all affected workstream agents before they resume.

Emergency breaks (security or REL-001) may be fixed immediately; the supervisor documents the break and notifies agents retroactively.

---

## 7. Output prohibitions (applies to all agents, all outputs)

Never include in any file, log, CI artifact, screenshot, commit message, PR description, comment, or agent handback:

- Real receipt images or extracted text from real receipts
- Owner email, address, date of birth, SSN, account or card numbers, bank identifiers
- Auth tokens, refresh tokens, or session values
- Signed object URLs or upload/download capabilities
- Service-account keys, client secrets, or API key values
- Raw model output from private evidence
- Real GCP project IDs, Cloud SQL instance identifiers, bucket names, or Firebase project IDs
- Personally identifiable financial history

Tests use **synthetic fixtures only**. Private evaluation manifests reference fixtures by opaque IDs; they do not enter the public repository.

---

## 8. Domain invariants all agents must preserve

1. An acknowledged receipt is **never lost** (REL-001).
2. `client_submission_key` is generated with `crypto.randomUUID()` on the client before the POST request.
3. Receipt assets are immutable after finalization; `storage_generation` is recorded and verified before extraction.
4. Model output never directly mutates authoritative records before schema and deterministic validation.
5. Raw, normalized, inferred, and validation values remain distinguishable; no silent repair.
6. Only legal processing and verification state transitions are allowed and audited.
7. One current revision exists per receipt after successful extraction; retries do not duplicate it.
8. The extraction runtime has no tools, credentials, browsing, or action authority.
9. Migrations run as a one-shot pre-deploy step; services never migrate at startup.
10. Worker extraction inputs are bounded by the ceilings in `docs/architecture/implementation-contracts.md`.

---

## 9. Stop and escalate conditions

Stop implementation and escalate to the supervisor (who escalates to the owner when necessary) if:

- A canonical artifact conflicts with the assigned packet.
- GCP/Firebase/Vertex quota, region, billing, or permission cannot support the planned path.
- Real-iPhone camera, HEIC, or direct-upload behavior invalidates the UX or architecture.
- Live model benchmarking cannot meet the structured-schema or arithmetic requirements.
- Safe implementation requires expanding a non-goal or removing a non-negotiable control.
- An agent needs to change another workstream's frozen contract without supervisor approval.
- Real secrets or prohibited private data are discovered in the repository, logs, prompts, or output.
- A migration, destructive operation, cloud deployment, or repository publication lacks authority.
- Failure injection shows any acknowledged-evidence loss or silent corruption path.

---

## 10. Evidence standard

Every material claim must be supported by at least one of:

- An explicit owner-approved requirement in a canonical document.
- A repository artifact, executable test, or direct observation.
- A measurement, benchmark, prototype, or controlled experiment.
- A clearly reasoned inference whose premises and uncertainty are stated.

"Best practice," model confidence, framework popularity, or unsupported future-scale predictions are **not sufficient** evidence.

Unknowns must be labeled as unknowns. Assumptions must have an owner, validation method, and decision deadline.

---

## 11. Logging and observability rules

Structured logs may include only fields in the approved schema (`docs/security/control-baseline.md` §5). They must never include request or response bodies, image bytes, object capability URLs, identity tokens, email addresses, receipt text, model raw output, account numbers, or unsanitized stack objects.

Privacy-safe synthetic events may appear in public CI artifacts. All private-evidence processing events remain in the private production environment.
