# DollarTrace — Open Items and Decision Register

**Status:** Active canonical register  
**Owner:** Yemane  
**Maintainer:** Codex operating lead  
**Created:** August 13, 2026  
**Last updated:** August 13, 2026

## 1. How to use this register

This file records accepted owner decisions and unresolved items that could affect product scope, delivery, risk, or operations. Conversation history is supporting context only. An item is not complete until its acceptance evidence is linked or summarized here.

Status values:

- `Accepted` — owner-approved and authoritative.
- `Open` — requires work or a decision.
- `Deferred` — intentionally postponed and non-blocking for current delivery.
- `Complete` — implemented and supported by evidence.
- `Superseded` — replaced by a later recorded decision.

## 2. Accepted decisions

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
