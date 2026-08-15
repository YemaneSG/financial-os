# DollarTrace — Open Items and Decision Register

**Status:** Active canonical register  
**Owner:** Yemane  
**Maintainer:** Codex operating lead  
**Created:** August 13, 2026  
**Last updated:** August 15, 2026

## 1. How to use this register

This file records accepted owner decisions and unresolved items that could affect product scope, delivery, risk, or operations. Conversation history is supporting context only. An item is not complete until its acceptance evidence is linked or summarized here.

Status values:

- `Accepted` — owner-approved and authoritative.
- `Open` — requires work or a decision.
- `Deferred` — intentionally postponed and non-blocking for current delivery.
- `Complete` — implemented and supported by evidence.
- `Superseded` — replaced by a later recorded decision.

## 2. Accepted decisions

### DT-DEC-003 — Mobile correction actions remain continuously reachable

| Field | Decision |
|---|---|
| Status | `Accepted` |
| Decision date | August 15, 2026 |
| Decision owner | Yemane |
| Outcome | Keep the correction form's primary save action fixed to the bottom of the mobile viewport throughout review, with iPhone safe-area clearance and enough document padding to prevent content obstruction. |
| Responsive boundary | Viewports below 768 px use the fixed action bar constrained to the 480 px application shell; wider viewports retain normal in-flow actions. |
| Interaction hierarchy | Save expands to the available mobile width; Cancel remains secondary; existing validation, submission, and disabled states are unchanged. |
| Scope boundary | Presentation-only refinement; no receipt data, API, authorization, revision, or infrastructure behavior changes. |
| Acceptance evidence | Frontend lint, TypeScript, all 138 unit tests, and the production PWA build must pass; the implementation release must also pass the existing CI, deployment, and security-header gates. |
| Rationale | A primary action placed only at the end of a long itemized receipt forces unnecessary scrolling and is not suitable for fast phone-based review. |

This decision replaces the ineffective end-of-form sticky behavior on mobile. It
does not introduce autosave or bypass any correction validation.

### DT-DEC-002 — Sprint 2A is human review and trusted correction

| Field | Decision |
|---|---|
| Status | `Accepted` |
| Decision date | August 14, 2026 |
| Decision owner | Yemane |
| Outcome | Correct a `needs_review` receipt through an owner-only mobile/laptop workflow and preserve the correction as an immutable, auditable `human_verified` revision. |
| Scope boundary | Review/correction only; reliability enhancements, new ingestion sources, matching, analytics, and the DollarTrace rename remain outside this slice. |
| Delivery model | Codex is product/scope/integration decision maker; Claude Code through Vertex AI supervises three independent standard Sonnet workstreams for backend/data, frontend/product, and security/verification. |
| Troubleshooting policy | Non-blockers: 15-minute diagnosis then document/defer. Blockers: 30 minutes or two materially different attempts, then stop and wait for the owner. No recursive review or debugging loops. |
| Implementation contract | `docs/implementation/execution-packets/sprint-2a-human-review.md` |
| Release evidence | Implemented at `b03863c`; CI and deployment passed in GitHub Actions runs `31860806179` and `31860806300`; owner completed a production correction and confirmed human verification. Private receipt values are intentionally omitted. |
| Rationale | Production capture is working; correction is the smallest next capability that converts uncertain extraction into trusted, analysis-ready data without delaying acquisition. |

This decision authorizes the additive human-review API and production deployment described by the execution packet. It does not authorize new data sources, destructive infrastructure changes, or weakening durability, privacy, or authorization controls.

### DT-DEC-001 — Product name: DollarTrace

| Field | Decision |
|---|---|
| Status | `Accepted` |
| Decision date | August 13, 2026 |
| Decision owner | Yemane |
| Product name | **DollarTrace** |
| Category descriptor | **Personal Financial OS** |
| Positioning line | **Account for every dollar.** |
| Rationale | The name is memorable, portfolio-ready, and directly represents the system's evidence-backed goal of tracing every dollar from source transaction to purchase details and supporting records. |
| Implementation timing | Deferred; the current product and infrastructure continue operating as Financial OS until DT-OPEN-001 is deliberately executed. |

This decision approves the name. It does not authorize an unplanned replacement of production infrastructure, deletion of cloud resources, loss of operational history, or a data migration.

## 3. Open and deferred items

### DT-OPEN-002 — Explainable receipt validation and discount semantics

| Field | Value |
|---|---|
| Status | `Complete — initial release and owner-acceptance refinement deployed and verified` |
| Priority | Current bounded product slice |
| Owner | Codex operating lead |
| Trigger | Owner approved Sprint 2B subject to the smart-guidance design recorded below; implementation begins only after the research proposal handback |
| Expected size | Small bounded vertical slice; no database migration expected |
| User impact before completion | Failed checks identify that review is needed but do not explain the exact difference or likely cause clearly enough for a fast human decision. |

#### Implementation checkpoint — August 14, 2026

The approved Sprint 2B slice is implemented and locally verified. The owner-only
receipt detail now returns bounded deterministic evidence and up to three ranked
proposals; the mobile review flow shows the signed difference, formatted candidate
amount, reason, live preview, explicit confirm-as-shown path, and the retained
arithmetic-exception state. Confirm-as-shown uses full-snapshot semantic equality,
exact decimal comparison, immutable child revisions, failed-finding retention,
stale-parent protection, and privacy-safe event reasons.

One non-blocking hypothesis remains deliberately deferred: a unique two-line
removal combination. The current engine handles receipt discounts, line discounts,
gross/net subtotal support, exact quantity-by-price corrections, and one-line
removal only when simulation restores a material equation. A two-line deletion
requires additional evidence and UI targeting to avoid presenting a coincidental
or destructive suggestion; it is not needed for the observed discount case and
does not block Sprint 2B release.

#### Owner-acceptance checkpoint — August 15, 2026

The deployed explanation correctly found the exact discount relationship, but it
ranked replacing the evidenced subtotal above preserving the receipt values.
Focused regression then disproved the initially considered clear-discount fix:
that edit balanced the total while creating a line-item/subtotal mismatch and
discarding discount evidence.

The accepted refinement recognizes two retailer discount conventions using
versioned deterministic checks. When complete line arithmetic proves the discount
is already included in subtotal, the strong action preserves both values and
confirms that interpretation; the live preview applies the discount once. Partial
line coverage cannot support a strong recommendation, and equally supported
choices remain ambiguous. Historical V1 findings stay readable. No migration,
provider, or infrastructure change is introduced.

#### Owner-observed problem

During Sprint 2A acceptance, a retailer discount appeared to be represented both
in the extracted subtotal or line items and as a separate receipt-level discount.
The system correctly detected an arithmetic inconsistency, but the review UI
showed only a technical check code and outcome. It did not show the equation,
calculated total, receipt total, difference, or the likely discount interpretation.

No real receipt value or private evidence is recorded in this public artifact.

#### Recommended outcome

Turn every arithmetic review flag into a short, deterministic explanation such
as: “Receipt total is X; the calculated total is Y; the difference is Z.” When
the difference equals a captured discount or matches the line-item/subtotal gap,
show a carefully worded possibility that the discount may already be included.
Never auto-delete or reinterpret a discount; the owner remains the decision maker.

#### Approved product conditions

- Reviewing a receipt must be a quick decision task, not a manual search task.
- The system must calculate and display the signed difference, then search totals,
  discounts, line amounts, and line arithmetic for evidence-backed matches.
- When a likely correction is found, the UI must identify the exact field or item,
  explain why it matches, and offer a one-tap draft correction for confirmation.
- A matching amount alone may be shown as a candidate but is not enough to
  recommend deletion. A strong recommendation must also restore the relevant
  line-item/subtotal and receipt-total equations.
- The owner must always have `Confirm as shown` and `Edit manually` alternatives.
  The manual path is a fallback, not the expected review workflow.
- Applying a suggestion changes only the editable preview. The immutable human
  revision is written only after explicit confirmation.

#### Smart candidate engine proposal

1. Build an exact integer-minor-unit reconciliation graph containing receipt
   components, gross and net line-item sums, receipt and line discounts, and
   quantity-by-unit-price calculations.
2. Generate bounded minimal-edit hypotheses: remove or restore a duplicated
   receipt discount; move a discount between receipt and line scope; correct a
   line whose quantity-by-price result is exact; or add/remove one line whose
   amount equals the signed discrepancy.
3. Consider a bounded two-line combination only when it is unique and closes
   both reconciliation equations. Do not perform an open-ended subset search
   that can manufacture coincidental explanations.
4. Rank candidates by deterministic evidence: exact discrepancy match, number of
   equations restored, discount/coupon/savings label evidence, adjacency to the
   affected item, uniqueness, and minimum edit count. Present evidence bands such
   as `Strong`, `Possible`, or `Ambiguous`; do not invent probability percentages.
5. Present at most three ranked action cards. Each card includes the difference,
   identified item or field, before/after equation, why it is proposed, and an
   `Apply and preview` action that immediately reruns all checks.

Example interaction using synthetic amounts:

> **Difference: $4.99**
>
> One line matches the gap: Item 7, “Example item,” $4.99. Removing it also makes
> the item sum equal the subtotal and the calculated total equal the receipt
> total. **Strong match.**
>
> `Apply and preview` · `Confirm as shown` · `Choose another`

When the evidence is not strong, the system says so and still shows the relevant
candidate rows. It never sends the owner back to scan the receipt unaided.

#### Confirm-as-shown semantics

`Confirm as shown` creates an immutable human revision that preserves the
evidenced values and retains the failed arithmetic finding. The verification axis
records that a human confirmed the evidence; it does not pretend the arithmetic
passed. The UI displays `Human confirmed — arithmetic exception`, and the
append-only state event uses a privacy-safe reason such as
`human_confirmed_exception`. The existing revision, finding, and event structures
can support this without a database migration; the current service rejection of
failed human revisions must be relaxed only for this explicit disposition.

#### Review-time target

- Strong proposal: target confirmation in 15 seconds or less after opening review.
- Ambiguous proposal: target a decision in 30 seconds or less using ranked choices
  or `Confirm as shown`.
- Measure proposal acceptance, rejection, manual-edit use, exception use, and
  review duration without logging receipt content or amounts.

#### Bounded Sprint 2B scope

1. Extend the owner-only receipt-detail contract to return the already persisted
   numeric `observed` and `expected` validation evidence using bounded schemas.
2. Add a deterministic line-item-sum versus subtotal check so the system can
   distinguish a total-component mismatch from a line-item/subtotal mismatch.
3. Replace internal-only validation output with plain-language equations,
   formatted currency differences, affected line numbers, and non-authoritative
   likely-cause guidance.
4. Show a live arithmetic preview in the correction form before submission so a
   proposed edit can be evaluated without a failed save attempt.
5. Add focused backend, contract, frontend, accessibility, regression, and
   privacy tests; publish through the existing CI and deployment workflow.

#### Acceptance evidence

- Every failed totals check displays receipt total, calculated total, signed
  difference, and the components used in the calculation.
- Every failed line-item check identifies the line and its observed versus
  calculated amount without exposing internal identifiers.
- Discount-related guidance is displayed only when proved by deterministic
  numeric relationships and is labeled as a possibility, not a correction.
- A reviewer can change or remove a discount and see the new equation before
  saving.
- Existing immutable-revision, owner-authorization, exact-money, and stale-write
  controls remain unchanged and green.
- No real receipt content, owner identity, or deployment identifier enters source
  control, logs, screenshots, or test fixtures.

#### Why this is the next easy win

The validator already persists most totals evidence, the review flow already
exists, and the change requires no new integration, infrastructure, background
job, model, or data migration. It closes the observed human-decision gap before
additional receipt automation or new financial sources increase review volume.

### DT-OPEN-001 — Execute the DollarTrace rename

| Field | Value |
|---|---|
| Status | `Deferred` |
| Priority | Next bounded maintenance/release window |
| Owner | Codex operating lead |
| Blocked by | Explicit start instruction for the rename window |
| Estimate | 2–4 autonomous hours, excluding propagation delays outside the repository |
| User impact before completion | None; the deployed Financial OS remains available |

#### Approved outcome

Present one coherent **DollarTrace** identity across the product UI, installable PWA, public portfolio documentation, source packages, and GitHub repository while preserving all financial data, stable contracts, security controls, and the working production deployment.

#### Naming contract

| Surface | Target |
|---|---|
| Human-facing product | `DollarTrace` |
| Product category | `Personal Financial OS` |
| GitHub repository | `dollartrace` |
| JavaScript workspace/package scope | `dollartrace` / `@dollartrace/web` |
| Python distribution and import package | `dollartrace` |
| Existing GCP/Firebase project identifiers and deployed resource IDs | Retain unless a separate migration is justified and approved |
| Existing production data, database records, object paths, and immutable evidence identifiers | Retain unchanged |
| Current provider-generated hosting URL | Retain; a branded custom domain is a separate future decision |

The distinction between brand names and infrastructure identity is intentional. Provider IDs and deployed resource names are not product branding and can be expensive, disruptive, or impossible to rename in place.

#### Autonomous execution plan

1. **Preflight and recovery point**
   - Confirm a clean worktree, synchronized `main`, working GitHub authentication, and current production health.
   - Record the current local commit, remote commit, deployed revisions, and non-secret resource references needed for rollback.
   - Create a dedicated `chore/dollartrace-rename` branch.
   - Run the repository private-data and secret checks before any publication step.

2. **Inventory and classify every old-name reference**
   - Classify occurrences as product copy, documentation, package/import namespace, contract identifier, observable metric/log field, deployment configuration, existing cloud resource, or historical evidence.
   - Preserve historical evidence statements where rewriting them would falsify what was deployed at the time.
   - Produce an explicit compatibility map for intentionally retained legacy infrastructure identifiers.

3. **Rename code and product surfaces**
   - Update PWA name, short name, page metadata, app copy, accessible labels, and synthetic tests.
   - Rename JavaScript package identities and lockfile references.
   - Rename the Python import package mechanically, update imports/configuration/tests, and preserve database schema and API behavior.
   - Update current documentation, contributor instructions, architecture labels, operational examples, and portfolio-facing text to DollarTrace.
   - Do not alter frozen HTTP/JSON contracts unless a brand string is purely descriptive and compatibility is unaffected.

4. **Protect production infrastructure and data**
   - Do not recreate the Firebase/GCP project, database, bucket, service accounts, queues, secrets, or durable storage merely to change their names.
   - Do not run Terraform if the plan proposes replacement or deletion of any stateful or security-sensitive resource.
   - Update safe display names and future-provisioning defaults only when the resulting plan is demonstrably non-destructive.
   - Keep legacy metric identifiers when renaming would break alert continuity; update human-readable dashboard labels separately.

5. **Verify before external changes**
   - Run backend unit, integration, contract, security, and synthetic end-to-end tests.
   - Run frontend lint, type-check, unit tests, and production build.
   - Run formatting, static checks, private-data scanning, secret scanning, and configuration validation.
   - Search for stale `Financial OS` variants and disposition every remaining occurrence as intentional or defective.
   - Exercise the local capture flow, including JPEG and HEIC/HEIF handling.

6. **Publish safely**
   - Commit the rename as a bounded change with an evidence summary.
   - Push the branch, then rename the private GitHub repository from `financial-os` to `dollartrace` and update the local SSH remote.
   - Rely on GitHub's redirect only as compatibility support; update canonical links to the new repository URL.
   - Merge only after all required checks pass.

7. **Release and validate**
   - Deploy the PWA branding first and verify the install name, manifest, cache behavior, security headers, authentication, upload, acknowledgement, and retrieval flow.
   - Deploy backend code only if the namespace rename changes its build artifact; use the existing immutable-image and rollback process.
   - Verify production health and one synthetic end-to-end receipt flow without placing private evidence in public artifacts.
   - Confirm that no Terraform or deployment action replaced stateful resources.

8. **Closeout**
   - Record test and deployment evidence, the final commit, GitHub remote, retained legacy identifiers, and any follow-up items.
   - Mark DT-OPEN-001 `Complete` only after local, remote, and production validation agree.
   - Leave the existing local workspace directory name unchanged during an active Codex session; rename it later only if it can be done without invalidating the workspace binding.

#### Release gates

The autonomous run must stop without merging or deploying if any of the following occurs:

- A test or private-data/secret scan fails.
- A planned infrastructure action would delete, replace, or orphan stateful resources.
- Authentication, receipt capture, durable acknowledgement, or HEIC/HEIF upload regresses.
- The GitHub rename targets the wrong repository or account.
- A frozen contract would require a breaking change.
- Required credentials or permissions are unavailable after safe retry and diagnosis.

#### Completion evidence

- All required automated checks pass.
- Local `main` and GitHub `main` resolve to the same verified commit.
- GitHub repository is named `YemaneSG/dollartrace` and the SSH remote matches.
- The installed/mobile web experience displays DollarTrace.
- Production health, security headers, authentication, and synthetic receipt capture pass.
- Production financial data and stateful cloud resources are unchanged.
- Every retained `financial-os`/`financial_os` identifier is listed as an intentional compatibility exception.

#### Rollback

- Revert the bounded rename commit or redeploy the last known-good immutable artifacts.
- Restore the prior GitHub repository name if repository-level routing fails.
- Restore the prior local remote URL.
- Do not roll back by deleting or recreating stateful cloud resources.

## 4. Decision log maintenance

New entries must include an owner, status, rationale or question, implementation impact, and acceptance evidence. Material product changes must also update the PRD or roadmap when this register alone would leave the canonical product contract ambiguous.
