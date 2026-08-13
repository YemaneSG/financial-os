# Financial OS — Technology and Deployment Recommendation

**Status:** Proposed Gate A review baseline  
**Decision owner:** Yemane  
**Prepared:** August 12, 2026

## 1. Recommendation

Use a **GCP-first managed modular monolith** for the first production acquisition system:

| Concern | Recommended default |
|---|---|
| Mobile client | React + TypeScript + Vite PWA |
| Static hosting | Firebase Hosting |
| Authentication | Firebase Authentication with Google sign-in and application allowlist |
| Public API | Python 3.12+, FastAPI, Pydantic |
| Private processing | Same Python application image, separate private Cloud Run worker service |
| Durable queue | Cloud Tasks with OIDC-authenticated worker delivery |
| Scheduled recovery | Cloud Scheduler invoking a private reconciliation handler |
| Relational data | Cloud SQL for PostgreSQL |
| Evidence | Private Google Cloud Storage bucket with short-lived object-specific upload/download capabilities |
| Extraction | Provider interface; initial current GA Vertex AI Gemini Flash-class multimodal adapter |
| Persistence code | SQLAlchemy 2 + Alembic; standard PostgreSQL-compatible schema |
| Secrets/identity | Google IAM, workload service accounts, Secret Manager only when identity cannot replace a secret |
| Container registry/runtime | Artifact Registry + Cloud Run |
| Infrastructure | Declarative Terraform/OpenTofu-compatible configuration |
| CI/CD | GitHub Actions with short-lived Workload Identity Federation |
| Tests | pytest, Vitest, Playwright, synthetic receipt fixtures |
| Code quality | Ruff, Pyright or mypy, ESLint, TypeScript strict mode |
| Observability | Structured logs, Cloud Logging/Monitoring, logs-based metrics and alerts |

The exact active model identifier, runtime versions, and infrastructure tiers are pinned during implementation preflight and recorded in source control. Avoid aliases whose behavior can change without a recorded evaluation.

## 2. Why this is the best current fit

### Speed

- Firebase Hosting provides managed HTTPS static delivery.
- Firebase Authentication provides federated sign-in and persistent web sessions; its web SDK supports local persistence across browser closure: [Firebase authentication persistence](https://firebase.google.com/docs/auth/web/auth-state-persistence).
- Cloud Run accepts ordinary containers and scales idle revisions to zero by default, reducing operational work at single-user volume: [Cloud Run autoscaling](https://docs.cloud.google.com/run/docs/about-instance-autoscaling).
- Cloud Tasks supplies authenticated delivery and retries without introducing Redis or a self-operated worker queue.

### Coherence with available resources

- The owner has access to a funded GCP/Vertex environment.
- The initial model and service identities can remain in one cloud permission system.
- Cloud Storage images can be passed to Vertex AI without downloading them through an unrelated provider.

### Portability

- React PWA uses browser standards.
- FastAPI is containerized.
- PostgreSQL and Alembic migrations are portable.
- Storage, queue, auth, and extractor remain application ports.
- The Mac Mini can implement local adapters or run the same container later.

### Data integrity

- PostgreSQL fits receipt revisions, line items, matching, statements, reconciliation, constraints, and transactions better than a document store.
- Direct private object upload separates large image bytes from API and database persistence.
- Queue delivery decouples five-second capture from multimodal extraction latency.

### Security

- Public, private-worker, evidence, database, and deployment identities can use least-privilege IAM.
- Cloud SQL supports automatic short-lived IAM database authentication through its Python connector, avoiding a permanent database password: [Cloud SQL IAM authentication](https://docs.cloud.google.com/sql/docs/postgres/iam-authentication).
- GitHub Actions can exchange OIDC assertions for short-lived GCP access instead of storing a service-account key: [Google Workload Identity Federation](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines) and [GitHub OIDC for GCP](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform).

## 3. Alternative assessment

Scores are directional for this approved product and current constraints, not universal rankings. `5` is strongest.

| Option | One-day speed | Durable async work | Relational fit | Security coherence | Mac portability | Current-resource fit | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| A. GCP managed modular monolith | 4 | 5 | 5 | 5 | 4 | 5 | 28 |
| B. Vercel + Supabase + separate AI provider | 5 | 3 | 5 | 3 | 4 | 3 | 23 |
| C. Laptop/local tunnel before Mac Mini | 2 | 2 | 4 | 2 | 5 | 3 | 18 |
| D. Native SwiftUI + custom backend | 2 | 4 | 5 | 4 | 4 | 4 | 23 |

### Option B — Vercel and Supabase

**Strength:** Fastest conventional web/BaaS assembly, managed PostgreSQL/auth/storage, good prototype ergonomics.

**Why not default:** Durable extraction still needs a queue/worker strategy; Vertex integration crosses control planes; later GCP and Mac Mini operations would span more providers. This remains the fallback if GCP permissions or Cloud SQL setup block the one-day outcome.

### Option C — Current computer and tunnel

**Strength:** Maximum local control and minimal cloud persistence.

**Why not default:** The owner explicitly permits cloud use, needs capture anywhere, and does not want the Mac Mini timeline to block acquisition. Laptop availability, sleep, networking, backups, and tunnel security add fragile operational dependencies.

### Option D — Native SwiftUI first

**Strength:** Best long-term native camera UX.

**Why not default:** App signing, Xcode workflow, and native implementation add day-one work without improving the core data pipeline. Stable APIs preserve SwiftUI as a later complementary client.

## 4. Stack decisions in detail

### 4.1 React/TypeScript PWA

Use React for a small stateful workflow—ordered images, upload progress, retry, authentication, history—and TypeScript strict mode for contracts. Vite keeps build/configuration small.

Do not add a full application framework, server rendering, global state library, or design system for the day-one client.

Use HTML Media Capture for the primary camera path. WebKit supports camera capture from file inputs and Home Screen web apps; a Web App Manifest and service worker improve the installed experience: [HTML Media Capture](https://webkit.org/blog/7477/new-web-features-in-safari-10-1/) and [iOS Home Screen web apps](https://webkit.org/blog/17333/webkit-features-in-safari-26-0/).

### 4.2 FastAPI modular monolith

FastAPI and Pydantic align with the original handoff, explicit API schemas, Python extraction tooling, and later analytics. Keep HTTP schemas separate from domain values where they differ.

One package produces:

- Public API entry point
- Private worker entry point
- Management/migration commands

Do not add separate repositories or independently versioned services.

### 4.3 PostgreSQL from day one

Use Cloud SQL PostgreSQL rather than SQLite in production because Cloud Run storage is ephemeral and the future domain is relational. Local tests may use PostgreSQL containers; SQLite substitution is not accepted for integration tests involving constraints or transaction behavior.

Use:

- SQLAlchemy 2
- Alembic migrations
- IAM DB authentication through the Cloud SQL Python connector in cloud
- Bounded connection pools and Cloud Run maximum instances
- Standard PostgreSQL types and features unless an ADR approves a provider-specific dependency

### 4.4 Direct object upload

The API creates object-specific short-lived upload capabilities after authenticating and authorizing the owner. The PWA uploads directly to Cloud Storage and asks the API to finalize.

Google documents signed URLs as time-limited permissions commonly used for uploads/downloads; anyone holding one can use it until expiration, so the design uses short lifetimes, opaque keys, TLS, and log redaction: [Cloud Storage signed URLs](https://docs.cloud.google.com/storage/docs/access-control/signed-urls).

### 4.5 Cloud Tasks worker

Use Cloud Tasks instead of in-process background tasks. A response from the upload request must not be responsible for keeping extraction alive. The task calls a private Cloud Run worker using OIDC. The worker and database enforce idempotency because queues provide at-least-once delivery behavior.

### 4.6 Vertex extraction adapter

Use a current GA multimodal Flash-class Gemini model only after a small receipt benchmark. Require structured JSON against a versioned schema. Retain exact model ID and raw output, then perform independent Pydantic and arithmetic validation.

Do not:

- Put the Vertex SDK in domain modules
- Treat model confidence as proof
- Give the extractor arbitrary tools
- Let receipt text alter system instructions
- Allow raw output to bypass validation

### 4.7 CI/CD and infrastructure

Sprint 0 establishes:

- Required PR checks
- Reproducible locked dependencies
- Pinned GitHub Action revisions
- Unit/integration/frontend test jobs
- Ruff/type/ESLint checks
- Secret and private-data scan
- Dependency audit
- Container build
- Infrastructure plan on pull requests
- Protected production deployment environment
- Workload Identity Federation constrained to the repository/environment

Do not use unpinned `@main` actions in a production pipeline.

## 5. Cost posture

- Cloud Run API and worker use request-based billing and minimum instances of zero initially unless real latency evidence requires one warm API instance.
- Set low maximum instance counts to protect Cloud SQL and bound unexpected spend.
- Static hosting, object storage, queue volume, and model calls should be small at single-user scale.
- Cloud SQL is the primary steady-state cost; select the smallest supported tier that meets backup and production requirements, then measure.
- Record per-receipt extraction latency and provider usage so model costs can be compared later.
- GCP project budget availability enables speed, but infrastructure still receives budgets/alerts and documented teardown for non-production environments.

## 6. One-day contingency ladder

Do not weaken evidence durability or authentication to save visual-polish time.

If the complete plan cannot fit the focused session, reduce in this order:

1. Visual polish and animations
2. Rich receipt history presentation
3. Derived-image enhancement beyond safe decode/EXIF removal
4. Infrastructure abstraction reuse
5. Automatic retry button polish

Do not remove:

- Owner authentication and allowlist
- Private storage
- Durable acknowledgement
- PostgreSQL metadata
- Explicit processing states
- Queue-backed processing
- Schema/arithmetic validation
- Provenance
- Critical-path tests

If GCP administrative permissions block progress, use the approved Option B fallback through a new reviewed execution-packet amendment rather than improvising an insecure public upload.

## 7. Decisions intentionally deferred

- Exact GA Vertex model ID pending benchmark and project availability
- Exact Cloud SQL tier and region pending quota/latency check
- Custom domain versus provider domain for the first private release
- Whether one warm API instance is justified by measured p95 capture time
- Advanced App Check/WAF controls after the baseline authenticated endpoint is measured
- Actual Budget integration until transaction ingestion architecture is reviewed
- Local Mac Mini runtime and replication mechanism

## 8. Gate A questions for independent reviewers

1. Does the recommended stack plausibly deliver the approved day-one outcome in one focused session?
2. Is splitting API and worker deployment from one codebase the smallest adequate trust boundary?
3. Does direct object upload improve reliability enough to justify its added handshake?
4. Are Cloud SQL and Cloud Tasks warranted immediately by accepted durability and async requirements?
5. Which proposed control, if any, adds ceremony without reducing a credible current risk?
6. Which missing constraint could invalidate the recommendation?
