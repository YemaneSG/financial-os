# Execution Packet — Production Receipt Capture Vertical Slice

**Status:** Ready for Gate A review  
**Packet owner:** Codex, for owner approval  
**Implementation lead:** Claude Code through Vertex AI  
**Date:** August 12, 2026  
**Repository revision:** `planning-baseline-2026-08-12-r1` until replaced by frozen commit

## 1. Outcome

When this work is complete, the owner can:

> Install the Financial OS PWA on an iPhone, authenticate, submit one or more ordered receipt photos, receive a truthful durable acknowledgement, and later retrieve validated structured receipt data or an explicit failure/review state.

## 2. Why now

High-quality financial intelligence requires longitudinal, item-level evidence. Receipt capture is the smallest daily behavior that starts collecting that evidence immediately while the transaction, matching, reconciliation, and future local-intelligence layers are developed separately.

## 3. Canonical inputs

Read these exact artifacts completely before planning or modifying code:

- `docs/product/PRD.md`
- `docs/product/roadmap.md`
- `docs/product/requirements-traceability.md`
- `docs/product/day-one-ux.md`
- `docs/architecture/system-architecture.md`
- `docs/architecture/data-architecture.md`
- `docs/architecture/technology-recommendation.md`
- `docs/security/threat-model.md`
- `docs/security/control-baseline.md`
- `docs/governance/ai-development-operating-model.md`
- `docs/implementation/sprint-0-1-plan.md`
- `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`
- `personal_ai_finance_codex_handoff.md`

This packet and the listed canonical artifacts are authoritative. Conversation history is supporting context only. If they conflict, stop and report the exact conflict before implementation.

## 4. Accepted decisions

- Day-one is a mobile-first installable PWA; SwiftUI is deferred.
- Initial production is managed GCP; the Mac Mini is a later incremental/replaceable runtime.
- Architecture is a portable modular monolith deployed as a public API and private worker from one backend codebase.
- Stack baseline is React/TypeScript/Vite, FastAPI/Pydantic, PostgreSQL/SQLAlchemy/Alembic, private Cloud Storage, Cloud Tasks, Cloud Run, Firebase Auth/Hosting, Vertex AI adapter, and declarative GCP infrastructure.
- Authentication is managed Google/federated identity plus exact single-owner allowlist and revocation.
- Upload is direct to private object storage using short-lived server-selected capabilities; finalization verifies evidence before acknowledgement.
- Acknowledgement means evidence and metadata are durably stored; extraction is asynchronous.
- Processing state and verification state are independent.
- Raw evidence, provider/model provenance, extraction attempts, deterministic validation findings, and revisions are retained.
- Original receipt images are retained indefinitely in V1; no automatic delete policy.
- Receipt/model content is untrusted data and the extraction runtime has no tools, credentials, browsing, or action authority.
- Personal finances only; rental itemization is deferred. Future obvious shared-card rental candidates are coarsely isolated and never classified solely by merchant without reviewable evidence.
- Provider-specific logic stays behind adapters. Domain and financial calculations remain deterministic and portable.

## 5. Scope

- Adapt the AI-project blueprint into a concise Financial OS repository structure without copying irrelevant ceremony.
- Build and deploy the authenticated iPhone PWA capture flow.
- Build the V1 receipt, asset, finalize, list, detail, retry, worker, reconciliation, health, and readiness contracts.
- Persist the V1 relational model and migrations.
- Implement private signed upload/download, durable tasking, extraction adapter, validation, state transitions, and minimal views.
- Implement CI/CD, least-privilege identities, infrastructure, observability, backup/restore, synthetic fixtures, and required controls.
- Produce real deployment and acceptance evidence.

## 6. Non-goals

- Bank/Plaid integration or financial-account credentials
- Amazon/email/Costco/statement/payroll source automation
- Receipt editing, correction, or review UI
- Transaction matching, reconciliation, categories as authoritative facts, or analytics
- Local LLM or Mac Mini deployment
- SwiftUI or Android native application
- Multi-user, sharing, rental itemization, or money movement
- Custom authentication, microservice expansion, event streaming, Kubernetes, or speculative scale machinery

Do not implement non-goals unless a newly discovered condition makes the approved outcome unsafe or impossible. Stop and escalate that condition before expanding scope.

## 7. Constraints and invariants

- `REL-001`: an acknowledged receipt is never lost.
- Only the owner reaches private data or expensive processing.
- The client never selects an arbitrary storage path or controls server identity fields.
- `client_submission_key` is unique per owner and returns the same logical receipt on replay.
- One receipt has one or more immutable, ordered evidence assets.
- Only legal processing and verification state transitions are allowed and audited.
- One promoted current revision exists per successful extraction generation; retries do not duplicate it.
- Money uses integer minor units for currency totals and decimal-safe arithmetic for quantity/unit calculations; no binary floats in financial calculations.
- Model output never directly mutates authoritative/current records before schema and deterministic validation.
- No silent repair: raw, normalized, inferred, and validation values remain distinguishable.
- Private data and credentials do not enter source control, public artifacts, prompts sent to unrelated agents, logs, or CI output.
- No runtime stores a long-lived GCP service-account key.
- Day-one `MUST` security controls are release blocking.

## 8. Required API and state contract

Minimum routes:

```text
POST /api/v1/receipts
POST /api/v1/receipts/{receipt_id}/finalize
GET  /api/v1/receipts
GET  /api/v1/receipts/{receipt_id}
POST /api/v1/receipts/{receipt_id}/retry-processing
POST /api/v1/receipts/{receipt_id}/assets/{asset_id}/download
POST /internal/v1/receipts/{receipt_id}/process
POST /internal/v1/reconcile-processing
GET  /health/live
GET  /health/ready
```

Internal processing states:

```text
reserved → uploading → uploaded → queued → processing → extracted
                                             ↘ retryable_failed → queued
                                             ↘ failed
```

Public states may collapse internal detail but must never imply completion that has not occurred. Verification is a separate dimension such as `unverified`, `system_validated`, `needs_review`, and later `human_verified`.

Contract changes after Wave 1 require supervisor approval, impact analysis, and affected-agent notification.

## 9. Acceptance evidence

The implementation lead must populate actual command, test path, environment, timestamp, and result for each row.

| Requirement set | Verification method | Required evidence |
|---|---|---|
| AUTH-001–004 | Auth integration tests plus installed-PWA session/revocation demo | Test output; redacted config/IAM evidence; screen recording or acceptance log |
| PWA-001, CAP-001–004 | Real iPhone install, camera, library fallback, multi-image draft flow | Device/iOS/browser conditions, timed acceptance record, synthetic screenshots if public |
| REC-001, UPL-001–004 | Concurrent idempotency, capability negative cases, partial retry, finalize failure injection | Integration-test results and state/object audit trail |
| QUE-001–002, STATE-001–002 | Queue authentication, duplicate delivery, stale work, retry/terminal tests | Test results, task policy, state-event evidence, age metric |
| EXT-001–004 | Fake-provider contract tests plus pinned live-provider benchmark | Provider/model/config record, schema adherence and latency report, provenance row |
| VAL-001–003 | Malformed, prompt-injected, weighted-item, discount, rounding, and inconsistent-total fixtures | Unit/evaluation results and resulting validation findings |
| VIEW-001–002 | Browser E2E from capture to history/detail with success/review/failure | E2E output and private acceptance record |
| RET-001–002, REL-001–003 | Restart/failure suite, backup/PITR config, isolated restore, DB/object inventory | Recovery record; zero-loss assertion; processing latency/terminal metrics |
| PERF-001, A11Y-001 | Timed Wi-Fi/cellular runs, automated scan, keyboard/VoiceOver-informed real-device review | Conditions and percentiles; accessibility report and resolved blockers |
| SEC-001–007 | Complete `MUST` control checklist and threat misuse cases | Security test output, policy/IAM/header/log evidence, signed reviewer verdict |
| SUP-001, PORT-001 | Clean CI, immutable container build, provider-adapter/domain boundary inspection | CI URL/run ID, image digest, container smoke test, architecture review |

Completion requires every row to pass or have an owner-approved, expiring exception that complies with `docs/security/control-baseline.md`.

## 10. Data and security considerations

**Data classes involved:** private financial evidence and normalized data; restricted credentials/configuration; public-development source/synthetic fixtures.

**Trust boundaries changed:** all TB1–TB9 boundaries in `docs/security/threat-model.md` are introduced by this slice.

**Secrets or credentials involved:** Firebase/GCP identity configuration, WIF trust, runtime service identities, possible provider configuration; use managed identity and Secret Manager only. Never print credential values.

**Required controls:** every day-one `MUST` in `docs/security/control-baseline.md`.

**Prohibited in source control, logs, CI, public screenshots, or agent handbacks:**

- real receipt images or text;
- owner email, address, date of birth, SSN, account/card numbers, bank identifiers;
- auth/access/refresh tokens;
- signed URLs or object capabilities;
- service-account keys, secret values, deploy credentials;
- raw model output produced from private evidence;
- private GCP project/resource identifiers in public portfolio artifacts.

## 11. Operational considerations

**Deployment impact:** creates a private single-owner production application and managed GCP resources. External provisioning/deployment occurs only after owner authorization.

**Observability:** privacy-safe structured events, outcome/latency/retry/age metrics, zero-loss invariant metric, safe error codes, budget alerts, service and queue failure alerts.

**Fallback:** owner keeps photos in the iPhone library when the service cannot truthfully acknowledge durability; later manual upload preserves acquisition.

**Rollback:** prior Firebase Hosting release and compatible Cloud Run revisions; pause queue; preserve objects/DB; expand-contract migration strategy; restore into isolation before destructive recovery.

**Migration/backfill:** initial schema only. No real historical backfill in this packet. Synthetic fixtures may seed a non-production environment; owner-private data enters only through the deployed authenticated product.

## 12. Parallel work plan

| Workstream | Owner/agent | Files or boundary owned | Inputs | Deliverable | Dependencies |
|---|---|---|---|---|---|
| Integration and contracts | Claude supervisor | Repository root instructions, frozen contracts, integration branch, final release evidence | All canonical inputs | Coherent integrated release | Gate A and platform preflight |
| Mobile PWA | Sonnet agent A | `apps/web/` and web tests/assets | Frozen OpenAPI/UX/config | Installable capture/status client | Wave 1 contracts |
| Receipt service | Sonnet agent B | `apps/api/`, `src/financial_os/`, migrations, server tests | Frozen domain/data/API contracts | API, worker, extraction, validation, persistence | Wave 1 contracts and infrastructure outputs |
| Platform/verification | Sonnet agent C | `infra/`, `.github/`, scripts/runbooks, synthetic E2E harness | Frozen services/config/control baseline | Secure deploy path, observability, recovery, acceptance harness | GCP/GitHub authority and Wave 1 outputs |

Do not parallelize shared schema, contract, migration, dependency-root, or configuration edits without the Claude supervisor as explicit integration owner. Agents submit proposed contract deltas rather than silently changing them.

## 13. Required checks

- [ ] Unit tests for domain, validation, state, idempotency, and adapters
- [ ] API/storage/queue/database integration and contract tests
- [ ] PWA component and browser E2E tests
- [ ] Real-device install/camera/library/network acceptance
- [ ] Formatting, lint, type checking, and migration validation
- [ ] Secret and private-data scanning
- [ ] Dependency, static security, and container scanning
- [ ] Threat-model misuse and negative authorization tests
- [ ] Accessibility and production-header checks
- [ ] Failure injection, queue retry, stale-work, and zero-loss assertions
- [ ] Backup/PITR configuration and isolated restore smoke test
- [ ] Immutable build/deploy and rollback evidence
- [ ] Product behavior demonstrated against every applicable requirement row
- [ ] Three independent Gate B reviews and finding disposition
- [ ] Documentation, architecture decisions, operational runbooks, and evidence index updated

## 14. Stop and escalate conditions

Stop implementation and return to the packet owner if:

- an accepted requirement conflicts with another canonical artifact;
- GCP/Firebase/Vertex region, quota, billing, or permission cannot support the proposed path;
- real-iPhone camera, HEIC, or direct-upload behavior invalidates the UX/architecture;
- live model benchmarking cannot meet structured schema or reasonable extraction behavior;
- safe implementation requires expanding a non-goal or removing a non-negotiable invariant/control;
- an agent needs to change another workstream's frozen contract without supervisor approval;
- real secrets or prohibited private data are discovered in the repository, logs, prompts, or output;
- a migration, destructive operation, cloud deployment, repository publication, or external side effect lacks authority;
- acceptance evidence cannot be produced as written;
- failure injection shows any acknowledged-evidence loss or silent corruption path.

Do not stop merely because a lower-priority visual feature is incomplete; apply the approved contingency ladder.

## 15. Handback contract

The Claude implementation lead returns:

1. Concise observable outcome summary
2. Exact files, contracts, migrations, infrastructure, and behavior changed
3. Frozen commit, image digest, deployed revision, and private endpoint references
4. Verification commands and complete result summary
5. Requirement/control evidence matrix with pass, fail, or approved exception
6. Independent review outputs and line-by-line finding disposition
7. Real-device acceptance conditions and results
8. Backup/restore, rollback, monitoring, and cost-control evidence
9. Known limitations, residual risks, and changed assumptions
10. Suggested next smallest slice based on observed evidence

Do not report completion based solely on generated code, passing unit tests, or a successful deployment.

## 16. Approval

**Product outcome and scope:** approved through completed PRD discovery  
**Planning baseline:** authorized for review by the owner's “perfect, let's go” direction  
**Implementation authorization:** pending Gate A and explicit cloud/repository access  
**Conditions:** preserve the one-day vertical slice, use evidence-backed independent reviews, and do not weaken the accepted durability/security invariants to move faster.
