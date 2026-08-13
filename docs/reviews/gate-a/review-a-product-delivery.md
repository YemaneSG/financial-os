# Independent Review — planning-baseline-2026-08-12-r1

**Review ID:** GATE-A-R1-A
**Reviewer charter:** Product and Delivery
**Reviewer model/tool:** claude-sonnet-4-6 / Claude Code Agent
**Date:** 2026-08-12
**Verdict:** Approve with conditions

---

## 1. Independence declaration

- I reviewed the artifacts listed below in an independent context.
- I did not receive or inspect another reviewer's conclusions before forming this verdict.
- I treated prior recommendations as claims to evaluate, not facts to inherit.
- I did not modify the reviewed artifacts.

No exception applies.

---

## 2. Review scope and immutable evidence packet

**Repository revision or artifact version:** planning-baseline-2026-08-12-r1

**Artifacts reviewed:**

- `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`
- `personal_ai_finance_codex_handoff.md`
- `docs/product/PRD.md`
- `docs/product/roadmap.md`
- `docs/product/requirements-traceability.md`
- `docs/product/day-one-ux.md`
- `docs/governance/ai-development-operating-model.md`
- `docs/architecture/system-architecture.md`
- `docs/architecture/data-architecture.md`
- `docs/architecture/technology-recommendation.md`
- `docs/security/threat-model.md`
- `docs/security/control-baseline.md`
- `docs/implementation/sprint-0-1-plan.md`
- `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md`
- `docs/governance/templates/independent-review.template.md`

**Explicitly out of scope:**

- Code that does not yet exist (implementation has not started)
- External service terms, billing, and quota confirmations (Wave 0 preflight items)
- Independent review of other reviewers' conclusions

---

## 3. Independent understanding

**The user problem**

Yemane spends money at retailers with mixed baskets — H-E-B, Costco, Amazon, restaurants — and obtains from current tools only a transaction-level record: merchant name, date, total. The actual purchase contents are invisible. This prevents granular questions ("how much did I spend on coffee?") and longitudinal item-level behavioral analysis. The problem is that the financial record is one abstraction layer too coarse to support the intended intelligence.

**The proposed outcome**

Build a private personal financial information system that captures item-level purchase evidence, stores it durably, extracts structured line-item data, and eventually connects it to a bank transaction spine, reconciliation, and a locally hosted language model for private financial analysis. The system must never expose financial credentials or move money autonomously.

**The smallest release**

Day one delivers one thing: an installable iPhone Progressive Web App that lets the owner photograph a receipt, submit it, receive durable acknowledgement within ten seconds, and later see structured extracted data or an explicit failure/review state. No analytics, no bank connections, no matching, no LLM. The value delivered is the start of a longitudinal item-level financial dataset and proof that the capture pipeline works at production quality.

**The system and implementation approach**

A portable modular monolith on GCP: React/TypeScript PWA hosted on Firebase Hosting, FastAPI API and private worker on Cloud Run (from one codebase), Cloud SQL PostgreSQL for structured records, private Cloud Storage for receipt evidence, Cloud Tasks for authenticated asynchronous extraction dispatch, Vertex AI Gemini Flash as the initial multimodal extractor behind a provider-neutral interface, Firebase Authentication for managed Google sign-in plus a server-side owner allowlist and session-version revocation. Infrastructure is declarative; CI/CD uses Workload Identity Federation. Three parallel Sonnet agents build the PWA, backend, and platform after the supervisor freezes contracts in Wave 1.

**The critical constraints**

- An acknowledged receipt is never lost (REL-001, the single hardest invariant).
- Only the allowlisted owner reaches private data.
- Processing state and verification state are independent; no automated process may assert human-verified status.
- Receipt text and model output are always untrusted data, never instructions.
- Money totals use integer minor units; no binary floating point in financial calculations.
- No runtime holds a long-lived GCP service-account key.
- Raw evidence, normalized data, extracted output, and validation findings remain independently attributable and preserved.
- Day-one scope does not expand unless a missing control makes the slice unsafe or inoperable.

---

## 4. Assumptions and unknowns

| ID | Assumption or unknown | Material impact | Evidence currently available | Required validation |
|---|---|---|---|---|
| A-1 | GCP project permits all required APIs (Firebase Auth/Hosting, Cloud Run, Cloud SQL, Cloud Storage, Cloud Tasks, Cloud Scheduler, Vertex AI, Secret Manager, Workload Identity Federation) in the intended region without quota blockers | Blocking if wrong; the entire stack collapses to Option B | The plan lists this as a Wave 0 preflight item and entry condition §4 | Owner confirms GCP project access and runs quota/API check before Wave 1 |
| A-2 | A current GA Vertex AI Gemini Flash-class multimodal model produces structurally valid, schema-adherent JSON extraction output at useful accuracy on representative grocery and retail receipts | If wrong, the extraction path fails and Sprint 1 cannot produce its stated user outcome | Plan includes a Wave 0 benchmark requirement; no results exist at planning-baseline time | Benchmark on synthetic plus owner-private representative fixtures before Wave 1; establish minimum schema-adherence and total-reconciliation rates |
| A-3 | iPhone camera uploads via direct signed URL to Cloud Storage succeed with HEIC images at realistic sizes, and Vertex AI can process the images (either directly from GCS URI or after worker-side conversion) | If either step fails, the primary capture path is broken | Architecture hypotheses §14 item 3 identifies this; no spike result exists yet | Spike test on owner's iPhone before Wave 1 |
| A-4 | Firebase Authentication persistent sessions work correctly in installed PWA / Home Screen context on the owner's iOS version | If sessions don't persist across PWA close/reopen, the ten-second capture target requires re-authentication each session | WebKit blog referenced in day-one-ux.md §8; no device-specific confirmation | Test AUTH-003 on owner's actual iPhone/iOS version before release |
| A-5 | Vertex AI's data handling terms and residency controls are acceptable for private financial receipt images processed by the owner's GCP account | If terms are unacceptable, a different extraction provider must be evaluated | Threat model accepts cloud processing; PRD §12.5 says verify terms before production reliance | Verify Vertex AI data processing addendum, image retention policy, and residency options during Wave 0 |
| A-6 | Cloud SQL provisioning, IAM database authentication, and initial Alembic migration can be completed within the one-session timeline | If Cloud SQL provisioning takes hours or has quota delays, Wave 1 stalls | Technology recommendation §4.3 and system architecture §14 list this; no confirmation | Confirm provisioning in Wave 0 preflight; select smallest tier meeting backup/PITR requirements |
| A-7 | Vertex API access through the owner's GCP/Vertex account is programmatic (project API key or service account), not dependent on a ChatGPT Plus or Claude Pro consumer subscription | PRD §12.5 explicitly flags this risk | Owner is said to have a funded GCP/Vertex environment; not confirmed as programmatic access | Confirm programmatic Vertex AI access and incremental cost per call before Wave 1 |
| A-8 | The owner has time to complete real-device iPhone acceptance (not only CI-passing) within the one-session window | Without this, the release gate cannot pass | Plan requires it in Wave 4 | Owner schedules iPhone availability for Wave 4 acceptance demonstration |

---

## 5. Strengths

| ID | Strength | Evidence | Why it matters |
|---|---|---|---|
| S-1 | Problem statement is precisely differentiated | personal_ai_finance_codex_handoff.md §1–2: "calorie tracking for money"; PRD §2: "account for every dollar and itemize every purchase wherever item-level evidence exists" | The differentiation from standard budgeting apps is specific, testable, and communicates the core technical requirement (item-level extraction) without ambiguity |
| S-2 | Day-one scope is genuinely minimal and defensible | PRD §13.2 lists 10 explicit exclusions from day one; roadmap sprint boundaries are outcome-labeled and non-calendar | Scope discipline prevents the scope-creep pattern common in personal-finance projects; the exclusions list is specific rather than vague |
| S-3 | "Capture first, analyze second" philosophy is correctly operationalized | PRD §5.1; roadmap delivery rules §2; execution packet §2; receipt capture Sprint 1, analytics Sprint 7, local LLM Sprint 8 | This sequence is the only one that creates real data before building intelligence, avoiding the common failure mode of building analysis tools on invented or insufficient data |
| S-4 | Adoption friction is addressed explicitly and measurably | day-one-ux.md §1–2: "receipt shutter button"; PRD §5.6 and §11.5: ten-second target under documented conditions; UX §6: record median and p95, not only best case | The ten-second target is specific enough to test and fail; the measurement methodology prevents cherry-picking |
| S-5 | All major future capabilities are credibly sequenced with no capability forgotten | Roadmap Sprints 3–9 cover: Plaid/transactions (S3), matching/reconciliation (S4), Amazon/email/Costco (S5), payroll/bills (S6), deterministic analytics (S7), local LLM (S8), Mac Mini (S9) | Reviewers cannot identify a significant capability from the blueprint that lacks a sprint slot, which means the roadmap is not optimistically pretending future work doesn't exist |
| S-6 | Provider replaceability is designed in structurally, not just described | system-architecture.md §4.7: `ReceiptExtractor` contract; §8: dependency direction enforcement; technology-recommendation.md §4.2: one package; data-architecture.md §1: four source-of-truth layers; PRD §5.7 | The interface boundary prevents extraction logic and financial semantics from becoming entangled with a specific vendor, which is the right architectural decision for an evolving AI landscape |
| S-7 | Failure recovery at every layer is explicit and non-optimistic | day-one-ux.md §5 failure table; system-architecture.md §6: what "saved" guarantees; §6.3: reconciliation sweep; execution packet §9 rollback procedures; UX principle: "Durability before celebration" | The design distinguishes what acknowledgement actually guarantees, which is the hard requirement for a trust-building product |
| S-8 | Verification state is honest by design | data-architecture.md §2 invariant 5 and §5.2; PRD §12.8: only explicit human action produces human_verified; control-baseline.md AI-03: no silent repair | Keeping verification state separate from processing state and never promoting model output to human-verified is the correct default for a financial evidence system |
| S-9 | Contingency ladder explicitly distinguishes what to cut from what to never cut | technology-recommendation.md §6 and sprint-0-1-plan.md §8 | The contingency ladder makes scope reduction decisions before pressure exists, which prevents under-time engineering choices from silently weakening durability or authorization |
| S-10 | The historical backfill policy prevents invented data | PRD §12.9: "Never invent historical line items from a merchant name, transaction category, typical basket, model inference, or unsupported assumption" | This rule makes financial-coverage and itemization-coverage metrics honest and independently measurable, which is essential for the portfolio credibility claim |

---

## 6. Findings

| ID | Severity | Finding | Evidence | Consequence | Required change | Verification |
|---|---|---|---|---|---|---|
| F-01 | Medium | The day-one release gate contains no minimum extraction quality criterion. A system where the Vertex AI adapter consistently produces schema-valid but uninformative extractions, or where all receipts land in `needs_review`, technically satisfies all day-one acceptance targets in PRD §11.5. | PRD §11.5 day-one targets: "100% of acknowledged uploads are durably stored and retrievable," "every upload reaches an explicit extracted, needs_review, or failed outcome," "95% complete processing within two minutes." None of these require a minimum rate of `extracted` or `system_validated` outcomes. PRD §11.5 explicitly states "A manually verified regression set of at least 50 varied receipts is established before field-level extraction-accuracy targets are finalized" — acknowledging targets are not yet set. | User adoption depends on seeing itemized data. If first-week usage produces a near-100% `needs_review` rate, the behavior-change goal (daily receipt capture) fails even though the infrastructure succeeds. The one-session timeline could be declared complete while delivering a product that does not yet produce item-level financial intelligence. | During Wave 0, the model benchmark (sprint-0-1-plan.md §5 Wave 0 item 4) must produce two minimum thresholds before Wave 1 proceeds: (a) the provider must demonstrate structured JSON schema adherence on at least a defined fraction of representative synthetic fixtures, and (b) the receipt total arithmetic check must be computable (not absent) on the majority of benchmarked receipts. These are minimum-bar criteria, not Sprint 2 accuracy targets. Add both criteria to Wave 0 exit conditions alongside "explicit pinned runtime choices." | Wave 0 exit evidence includes: benchmark report citing schema-adherence rate and arithmetic-computable rate against documented synthetic fixtures; these rates meet the stated minimums; or benchmark reveals a blocker requiring a different provider or approach, which triggers the stop-and-escalate condition already defined in execution packet §14. |
| F-02 | Medium | The Wave 0 technical preflight items — specifically the model benchmark and the iPhone HEIC/direct-upload spike — are described in sprint-0-1-plan.md §5 Wave 0 but are not listed as formal named entry conditions in §4. The §4 entry conditions cover Gate A and GCP access authorization but not the technical platform confirmations. | sprint-0-1-plan.md §4 entry conditions: lists Gate A, GCP access, GCP quota/API validation — but does not explicitly list "model benchmark completed with result above minimum quality bar" or "iPhone camera/HEIC/upload spike completed without blocking behavior." The stop-and-escalate conditions in execution packet §14 cover these, but they are reactive (stop if a blocker appears) rather than proactive (confirm before implementation starts). The Wave 0 exit criteria say "no known platform blocker" but Wave 0 activities and implementation-session Wave 1 activities are described sequentially in the same section, which could be read as occurring in the same session. | If the benchmark or spike is deferred to mid-session, a blocker discovered after Wave 1 contracts are frozen and parallel agents have started work requires costly rework and amendment. The "one focused implementation session" objective becomes a multi-session affair. | Add two named entry conditions to sprint-0-1-plan.md §4: (a) "Model benchmark completed; Wave 0 exit criteria met including minimum extraction quality thresholds" and (b) "iPhone HEIC/JPEG camera-to-signed-upload spike completed without blocking behavior." This creates an unambiguous pre-condition for starting Wave 1 and separates Wave 0 (Gate A + technical preflight) from Wave 1 (contract freeze and implementation start). | The updated sprint-0-1-plan.md §4 lists both conditions; the Wave 0 documentation includes a dated result for each; Wave 1 does not begin until both results are recorded. |
| F-03 | Medium | The two founding handoff documents (MAC_MINI_FINANCIAL_OS_BLUEPRINT.md and personal_ai_finance_codex_handoff.md) are listed as "canonical inputs" in execution-packet §3 alongside the PRD, architecture, and security documents. The blueprint describes a different operational system (Actual Budget as the ledger, Plaid directly serving as the connector, rental management as near-term, local LLM phases 7–8 of 8) from what day-one builds. An implementation agent reading the blueprint's Phase 2 ("Install Actual Budget, bind to local/private access only, create personal and rental ledgers") alongside the execution packet could question whether Actual Budget setup is required for day one, even though it is not. | MAC_MINI_FINANCIAL_OS_BLUEPRINT.md §15 Phase 2: "Install a stable release of Actual Budget... create personal and rental ledgers"; Phase 4: "Build automated ingestion" using the connector pattern. personal_ai_finance_codex_handoff.md §5 §6 defines V1 as five capabilities distinct from the current PRD's day-one. PRD §16 says the handoff documents "remain source material while this PRD consolidates decisions through product discovery." Execution packet §3 says "this packet and the listed canonical artifacts are authoritative" and "if they conflict, stop and report the exact conflict." | An implementation agent that stops to report a conflict between the blueprint's Phase 2 and the PRD's day-one scope wastes time during the focused session. More importantly, an agent that resolves the conflict incorrectly could attempt to configure Actual Budget or design a Plaid connection as a prerequisite, pulling future-roadmap scope into the one-day implementation. | Add an explicit precedence annotation to execution-packet §3: "In all cases of conflict between handoff source documents and the PRD, roadmap, architecture, threat model, or control baseline, the latter group of canonical product and architecture documents supersedes the handoff source documents. The handoff documents capture early design thinking and must not be treated as implementation instructions." This annotation requires no substantive changes to any artifact. | The execution packet §3 contains the precedence note; a new implementation agent session seeded with the updated packet does not flag Actual Budget, Plaid, or rental management as day-one scope conflicts. |
| F-04 | Advisory | "One focused implementation session" is used in multiple artifacts but is never explicitly defined to mean Waves 1–4 only, with Wave 0 occurring earlier. A reader could interpret Wave 0 (Gate A review synthesis + 5 preflight items including real-device testing) as part of the same session. | sprint-0-1-plan.md §8 delivery target: "One focused implementation session after Gate A approval." §5 Wave 0: described as the first wave without a clear separator from Wave 1. Sprint-0-1-plan.md §6 critical path diagram does show Gate A before GCP/iPhone preflight before contract freeze, implying sequential pre-work — but the text of Wave 0 mixes Gate A review (now happening) with preflight tasks (can happen in parallel with review synthesis). | This is ambiguity rather than error, but it could cause the owner to set an incorrect expectation about what a "one-day session" means, and then feel the project is behind when Gate A synthesis plus preflight consume a day before implementation starts. | In sprint-0-1-plan.md, relabel Wave 0 as "Pre-session: Gate A and platform preflight" and explicitly note that the "one focused implementation session" begins at Wave 1 after all pre-session exit criteria are met. No substantive technical change required. | Updated plan clearly labels pre-session and session phases; owner understands the timeline before authorizing cloud access. |
| F-05 | Advisory | The execution packet states that if GCP blocks progress, the Option B (Vercel + Supabase) fallback is invoked through "a new reviewed execution-packet amendment." The technology recommendation §6 says the same. This process could add meaningful overhead during the focused session if GCP fails at Wave 1. | technology-recommendation.md §3 Option B: "This remains the fallback if GCP permissions or Cloud SQL setup block the one-day outcome." Execution packet §5: "If GCP administrative permissions block progress, stop and amend the execution packet to the already-evaluated managed fallback." The term "new reviewed execution-packet amendment" is not defined — it could mean a lightweight operating-lead decision or a full three-reviewer gate. | If GCP fails during the implementation session, the team stops to produce an amendment, which requires some review cycle. If that cycle takes hours, the "one focused session" objective is defeated. Option B is already evaluated and scored (technology-recommendation.md §3); it does not require re-evaluation of the core product decision, only the deployment topology. | Add an appendix or note to the execution packet that pre-authorizes Option B activation at the operating lead's discretion (not requiring a new Gate A-level review) if GCP access or Cloud SQL provisioning is confirmed blocked during Wave 0 preflight, subject to owner notification. The note should specify the exact trigger condition: "GCP admin permissions or Cloud SQL provisioning cannot be resolved within [defined timeframe]." | Pre-authorization note exists; if Option B is invoked, the operating lead notifies the owner and documents the trigger and substitution in the execution packet amendment before Wave 1 proceeds. |
| F-06 | Advisory | The day-one performance requirement (PERF-001: ten seconds, single-photo, documented conditions) requires "real-device timed test on Wi-Fi and cellular" as verification, and the UX document §6 specifies what to record per-run. However, no minimum sample size is stated. A single successful ten-second run satisfies the acceptance criterion as written. | day-one-ux.md §6: "record device and iOS version, network type, image dimensions and bytes, time to preview, upload duration, finalization duration, total workflow duration. Report median and p95." No run count specified. requirements-traceability.md PERF-001: "Real-device timed acceptance and processing benchmark." | A single favorable run cannot produce a valid median or p95. The acceptance criterion appears more rigorous than it is. For a product where capture speed is a core adoption driver, a one-run sample is not credible evidence. | Specify a minimum sample: at minimum 10 timed runs per network type (Wi-Fi, cellular), each with a different receipt image and freshly opened PWA, before reporting median and p95. Add this to the acceptance evidence row for PERF-001 in the execution packet §9. | Acceptance evidence for PERF-001 includes a table of at least 10 runs per network type; median and p95 are computable from the recorded samples. |
| F-07 | Advisory | The extraction schema allows `category_suggestion` as a non-authoritative initial category in `line_item_revisions`, but no category taxonomy or suggestion vocabulary is specified for the extraction prompt. Different extraction runs on similar items may produce inconsistent category labels (e.g., "Groceries > Produce," "Food > Vegetables," "Grocery"), which degrades the day-one value for anyone looking at extracted data and complicates later category normalization. | data-architecture.md §4.7: `category_suggestion text nullable`: "Non-authoritative initial category." No accompanying taxonomy. personal_ai_finance_codex_handoff.md §18 defines a candidate taxonomy but it is in the handoff document (not a canonical document for day-one implementation). requirements-traceability.md EXT-003: "Each line item can preserve...category suggestion." No reference to a vocabulary constraint. | Inconsistent category suggestions in day-one data are annoying but not damaging, since categories are non-authoritative. However, if many receipts enter the system with inconsistent AI-suggested categories, normalizing them later requires a migration or a manual review pass. This is low priority for one user, but the cleanup cost grows with data volume. | Add a versioned minimal category vocabulary to the extraction-prompt specification (a simple flat list of 15–20 values such as Groceries-Produce, Groceries-Protein, Groceries-Pantry, Dining, Transportation, Health, Outdoors, Household, Technology, Subscription, Other). The vocabulary does not need to be hierarchical for day one; it only needs to be consistent across extraction runs. Add vocabulary version to the `extraction_runs.prompt_version` field coverage. | Extraction prompt specification includes the vocabulary; two extraction runs on the same receipt type use the same category labels from the defined set; vocabulary version is recorded in extraction_runs. |

---

## 7. Adversarial checks performed

| Concern tested | Evidence examined | Conclusion |
|---|---|---|
| Does the BLUEPRINT document contaminate day-one scope with Actual Budget, rental management, or Plaid as prerequisites? | MAC_MINI_FINANCIAL_OS_BLUEPRINT.md §15 Phases 2–4; PRD §13.2 and §14; execution packet §3 precedence language; roadmap Sprint 3 for Plaid | Contamination is not present in the approved design. The PRD explicitly defers Actual Budget, Plaid, rental management, and the local LLM. The risk is that implementation agents reading both blueprint and execution packet could flag conflicts. Addressed as F-03 (Medium). |
| Is the day-one extraction quality gate sufficient to prove user value? | PRD §11.5 day-one targets; roadmap Sprint 1 exit evidence; personal_ai_finance_codex_handoff.md §42 ("first emotionally satisfying milestone"); Wave 0 benchmark requirement | The release gate is infrastructure-focused and does not require extraction accuracy. This is intentional under the "capture first" philosophy, but creates a gap if the benchmark is omitted or produces no minimum threshold. Addressed as F-01 (Medium). |
| Does the "one focused day" timeline misrepresent what will actually be achieved? | sprint-0-1-plan.md §5 Wave structure; three parallel Sonnet agents; contingency ladder; scope exclusions list | With parallel AI agents and pre-frozen contracts, the scope is plausible in an extended implementation session. However, Wave 0 must be complete before the session begins; the session itself is Waves 1–4. The ambiguity is a clarity issue, not a dishonesty issue. Addressed as F-04 (Advisory). |
| Does any architecture decision irreversibly block the Mac Mini, local LLM, or Plaid integration? | system-architecture.md §12; technology-recommendation.md §2 portability; data-architecture.md §10–11; PRD §5.7; blueprint §4 core design principle | No blocking decision found. The extraction adapter, auth boundary, storage port, and PostgreSQL schema are all designed for replaceability. The local LLM receives only an allowlisted read-only query service (Sprint 8), consistent with the blueprint's security principle. |
| Is there an authorization path for a non-owner Google account to reach private data? | threat-model.md T-01; control-baseline.md IAM-01; requirements-traceability.md AUTH-001; system-architecture.md §9 | The design correctly requires server-side Firebase token verification AND a server-side owner allowlist on every private request. A valid non-owner Google token produces a 403. The test IT-AUTH-001 explicitly covers this. |
| Can the private worker be invoked directly by an external actor? | threat-model.md T-09; control-baseline.md QUE-01, NET-01; system-architecture.md §4.3; technology-recommendation.md §4.5 | The worker uses Cloud Run private ingress; only the Cloud Tasks OIDC identity and Cloud Scheduler OIDC identity can invoke it. Direct public invocation is blocked. Test coverage is specified. |
| Can receipt text escape the data boundary and become an instruction to the extractor or API? | threat-model.md T-06 (High/High); control-baseline.md AI-01/02/03; system-architecture.md §9; misuse case 6 | The extractor has no tools, no credentials, no browsing, and no arbitrary URL fetch authority. It receives images and returns structured JSON against a versioned schema. The worker enforces schema validation before any output reaches the database. Prompt-injection fixtures are required in the acceptance checklist. |
| Does the Plaid/transaction integration depend on an unreviewed external architecture assumption that could break day-one choices? | roadmap Sprint 3 scope; PRD §12.10; data-architecture.md §10; control-baseline.md scope-triggered controls for Plaid | Sprint 3 adds source-neutral tables (`transactions`, `transaction_imports`) and a connector evaluation step. The day-one schema's `receipt_assets` and `receipt_revisions` tables do not assume Plaid compatibility, and the matching relationship in Sprint 4 is designed for many-to-many. No day-one decision precludes Sprint 3. |
| Are the Amazon/email/payroll/Costco capabilities plausibly sequenced rather than optimistically ignored? | roadmap Sprints 5–6; PRD §7–8 acquisition table; PRD §12.10 source automation priority | All secondary sources are scheduled with explicit sprint assignments. Amazon (S5), email (S5), Costco (S5), payroll/pay stubs (S6), utilities (S6). Each begins with a manual fallback requirement before automation. None are missing from the roadmap. |
| Is the metric design honest — specifically, can itemization coverage be gamed by claiming item-level evidence for transactions that lack it? | PRD §12.9 evidence-only backfill policy; data-architecture.md §2 invariant 12; PRD §11.2 eligibility definition | The PRD explicitly prohibits invented historical line items and requires unitemized transactions to remain explicitly unitemized. Coverage metrics have separate denominators for financial coverage and itemization coverage. Eligibility exclusions for transactions that cannot have item-level evidence are specified as required PRD work before metrics are operationalized. Honest by design. |
| Is there a silently missing recovery path for acknowledged evidence loss? | control-baseline.md REL-001, API-03, DB-03; system-architecture.md §6.3; threat-model.md T-12 | The reconciliation sweep, object versioning/retention, PostgreSQL PITR, and restore smoke test collectively address evidence loss. The architectural guarantee is: acknowledgement is only issued after objects are verified in storage AND durable state is recorded in the database. The failure-injection test suite is required before release. |
| Does the authentication design have a gap for session persistence across PWA close/reopen? | day-one-ux.md §8; requirements-traceability.md AUTH-003; technology-recommendation.md §2 Firebase persistence | Firebase Authentication's web SDK with local persistence (`LOCAL` persistence mode) maintains the refresh token across browser closure. AUTH-003 requires a close/reopen test on the installed PWA. This is device-specific and correctly listed as a required acceptance test rather than assumed. |
| Are the financial canonical rules (PRD §10) correctly enforced by the data model? | PRD §10 rules 1–12; data-architecture.md §7 money/time; data-architecture.md §2 invariants | All twelve canonical rules have representation: credit-card payments are deferred to Sprint 3 transfer recognition; duplicate pending/posted states are handled by the idempotency design; restaurant tip variance is representable in the revision schema; multi-image receipts are supported through `receipt_assets.ordinal`. No rule is incompatible with the day-one design. |

---

## 8. Residual risks

| Risk | Likelihood | Impact | Current control | Owner |
|---|---|---|---|---|
| Vertex AI benchmark meets minimum quality bar but production receipts (different lighting, handwriting, thermal paper) perform materially worse, leading to a high `needs_review` rate in first-week use | Medium | Medium — capture habit breaks if corrections are too frequent | Wave 0 benchmark with diverse receipt types; Sprint 2 regression set establishment; "capture first" philosophy tolerates review-required state | Yemane and operating lead; review in Sprint 2 with real data evidence |
| Cloud SQL provisioning requires quota increase or regional availability confirmation that delays Wave 1 by hours | Medium | Low-Medium — delays but not a product risk; Option B is the fallback | Wave 0 preflight confirms quota/region; contingency ladder eliminates Cloud SQL before removing authentication or durability | Operating lead; escalate immediately if quota is not confirmed in Wave 0 |
| HEIC-to-JPEG conversion in the Python worker creates an external dependency (e.g., `pillow-heif`) with non-trivial installation requirements on Cloud Run | Low-Medium | Low — solvable but delays integration; alternatively PWA-side JPEG conversion before upload could be substituted | Wave 0 iPhone spike tests the end-to-end path; worker architecture allows derived-image creation separate from originals | Receipt service agent; resolve during Wave 0 spike |
| Firebase Authentication persistent session behavior in iOS Home Screen mode changes across iOS/WebKit updates | Low | Medium — session loss is friction, not data loss; recovery path is re-authentication | AUTH-003 acceptance test on owner's exact iOS version; retested on major iOS updates | Operating lead after each major iOS release |
| Vertex AI terms for financial receipt images include a data-use provision the owner finds unacceptable | Low | High — requires provider change or local preprocessing before Vertex call | Wave 0 preflight includes terms verification; threat model accepts managed-cloud processing with explicit per-run provenance recording | Yemane; escalate if terms conflict during Wave 0 |
| Indefinite V1 image retention (PRD §12.6) creates a growing storage cost that is not noticed until months of daily capture accumulate | Low | Low — cost manageable at single-user scale initially; policy is configurable | OPS-01 budget alerts; technology recommendation §5 cost posture; Sprint 2–3 includes explicit retention review trigger | Operating lead; measure monthly storage volume starting at week four |
| The three parallel Sonnet agents in Wave 2 introduce an integration conflict on a shared schema or API contract despite the supervisor-only-changes rule | Low-Medium | Medium — integration rework delays Wave 3; not a data safety risk | Supervisor freezes all shared contracts before agents start; agents submit proposed changes rather than making them; supervisor owns integration branch | Claude supervisor in Wave 2; escalate any proposed contract change immediately |

---

## 9. Verdict rationale

**Verdict:** Approve with conditions

**Rationale:**

The planning baseline demonstrates coherent product thinking at the appropriate level of detail for a Gate A planning review. The user problem is specific, differentiated, and verifiable. The day-one scope is genuinely the smallest slice that starts building the longitudinal item-level financial dataset — the system's core durable asset. Future capabilities (Plaid, Amazon, payroll, Mac Mini, local LLM) are all present in the roadmap with plausible sequencing and no capability is accidentally pulled into day one or irreversibly blocked by day-one decisions.

The architecture is a defensible, portable modular monolith that correctly separates the extraction adapter, auth boundary, storage port, and financial domain from vendor-specific implementations. The data model's invariants (immutable revisions, independent processing and verification states, integer minor-unit money, no silent repair) are correct for a financial evidence system. The security model covers all material threats at proportionate severity, and the control baseline is organized to make release blocking controls verifiable.

The adoption friction analysis is rigorous — the ten-second target is measurable, documented, and failure is observable. The failure recovery design at every layer (retry without photo loss, reconciliation sweep, acknowledgement-only-after-durable) builds the kind of trust that sustains daily capture behavior.

Three medium findings require resolution before implementation begins, but none is architecturally disqualifying:

F-01 (extraction quality floor) is resolved by adding minimum quality criteria to the Wave 0 benchmark exit conditions — a planning clarification requiring no code change. F-02 (preflight entry conditions) requires adding two lines to the sprint plan's entry conditions list. F-03 (handoff document precedence) requires one paragraph of precedence language in the execution packet.

The plan does not dishonestly compress scope: the contingency ladder explicitly identifies what to cut vs. what is non-negotiable, and the stop-and-escalate conditions are specific enough to be actionable. The metric design is honest — verification state is separated from processing state, coverage denominators are not yet finalized (correctly, per the evidence-only policy), and itemization coverage cannot be inflated by inventing unverifiable line items.

The remaining residual risks (extraction quality on production receipts, HEIC handling, session persistence, Vertex terms) are appropriate for a single-owner system at this scale and are correctly owned with defined escalation paths.

**Conditions:**

| Condition | Owner | Deadline/gate | Verification |
|---|---|---|---|
| C-1: The Wave 0 model benchmark must produce explicit minimum thresholds for schema adherence rate and arithmetic-computable rate on representative synthetic fixtures before Wave 1 proceeds. These thresholds must be recorded in the Wave 0 exit documentation and, if not met, must trigger the stop-and-escalate condition rather than allowing implementation to continue with a failing provider. | Operating lead (Codex) | Wave 0 exit; before Wave 1 begins | Wave 0 exit documentation includes: provider model ID, benchmark fixture set description, schema adherence rate, arithmetic-total-present rate, latency distribution, minimum thresholds, and pass/fail determination. |
| C-2: Add two named entry conditions to sprint-0-1-plan.md §4: (a) "Model benchmark completed and minimum quality thresholds met or a blocker documented" and (b) "iPhone HEIC/JPEG camera-to-signed-upload spike completed without blocking behavior, or a documented design response to any blocking behavior." These must appear in the entry conditions list alongside the existing GCP access confirmation. | Operating lead (Codex) | Before the execution packet is handed to the implementation lead | Updated sprint-0-1-plan.md §4 lists both conditions; a new implementation agent session initiated from the updated packet does not proceed to Wave 1 without both items confirmed. |
| C-3: Add a precedence annotation to execution-packet §3 explicitly stating that in any conflict between the handoff source documents (MAC_MINI_FINANCIAL_OS_BLUEPRINT.md, personal_ai_finance_codex_handoff.md) and the canonical product and architecture documents (PRD, roadmap, architecture, threat model, control baseline), the latter group supersedes. | Operating lead (Codex) | Before the execution packet is handed to the implementation lead | Updated execution packet §3 contains the annotation; the change is reviewed for completeness before being distributed to implementation agents. |

---

## 10. Sign-off

This verdict applies only to the artifact versions listed in this review under planning-baseline-2026-08-12-r1. Material changes to the PRD, architecture, threat model, or execution packet invalidate affected conclusions and require targeted re-review of the affected finding areas.

The three conditions above are planning-level clarifications. They do not require new code, infrastructure changes, or owner approval of altered product intent. They can be resolved by the operating lead before the implementation session begins.

Advisory findings F-04 through F-07 enter the backlog. None blocks this gate.

**Reviewer:** claude-sonnet-4-6 / Claude Code Agent — GATE-A-R1-A (Product and Delivery)
**Timestamp:** 2026-08-12
