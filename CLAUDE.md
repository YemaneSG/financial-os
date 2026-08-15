# CLAUDE.md — Financial OS

> This file is a Claude Code adapter. Canonical policy is in `AGENTS.md` and `docs/governance/ai-development-operating-model.md`. This file does not override either.

---

## What this project is

A private, single-owner installable iPhone PWA that captures receipt photos and produces durable structured financial data. The backend is a portable modular monolith on managed GCP.

Day-one outcome: install → authenticate → photograph → upload → durable acknowledgement → structured data or explicit failure state.

---

## Canonical documents — read these before planning

| Priority | Document |
|---|---|
| 1 (security floor) | `docs/security/control-baseline.md` |
| 2 (product) | `docs/product/PRD.md`, `docs/product/roadmap.md` |
| 3 (architecture) | `docs/architecture/system-architecture.md`, `docs/architecture/data-architecture.md` |
| 4 (implementation) | `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md`, `docs/architecture/implementation-contracts.md` |
| 5 (governance) | `docs/governance/ai-development-operating-model.md` |
| Supporting context | `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`, `personal_ai_finance_codex_handoff.md` — superseded by tiers 1–5 |

---

## Stack — non-negotiable

- **Frontend:** React 18 / TypeScript / Vite — PWA targeting iPhone Safari
- **Backend:** FastAPI / Pydantic v2 / Python 3.12
- **Database:** PostgreSQL via SQLAlchemy 2.x async + Alembic migrations
- **Auth:** Firebase Authentication (Google sign-in) + server-side owner allowlist
- **Storage:** Cloud Storage (private bucket, signed capabilities)
- **Queue:** Cloud Tasks (authenticated OIDC delivery)
- **AI:** Vertex AI Gemini Flash-class adapter behind `ReceiptExtractor` interface
- **Deployment:** Cloud Run (API + worker) + Firebase Hosting (PWA) + declarative Terraform
- **Secrets:** Secret Manager only — no long-lived service-account keys
- **CI:** GitHub Actions with Workload Identity Federation

---

## Session protocol

When a bounded, owner-approved execution packet or explicit session objective is supplied:

1. Read the packet and canonical documents.
2. Restate the outcome, constraints, and evidence in the work log.
3. Proceed autonomously within the authorized scope; do not pause to ask for the goal again.

When no bounded packet or explicit objective is supplied:

1. Read `docs/open-items.md` (offer to create if absent).
2. Print a brief: blockers / open decisions / ready items.
3. Ask: "What is the goal for this session?" Wait for the answer.
4. Do not start implementing until the goal is confirmed.

Use `/session-start` to trigger this.

---

## Domain rules Claude must always apply

- `client_submission_key` is generated with `crypto.randomUUID()` on the client before the POST request. Never server-generated; never reused across owners.
- All currency totals are **integer minor units** (e.g., cents). `NUMERIC`/`Decimal` for quantities and unit prices. Never `float` for money.
- Model output never promotes to a current revision before schema validation and deterministic arithmetic checks.
- Raw, normalized, inferred, and corrected values stay distinguishable. No silent repair.
- Migrations run as a one-shot pre-deploy step. Services never call `alembic upgrade head` at startup.
- Extraction runtime has no tools, credentials, browsing, or action authority.
- Worker reads assets by recorded `storage_generation`; mismatches are terminal failures.

---

For work after Wave 1, also read the current owner-approved packet in `docs/implementation/execution-packets/`. Its bounded scope supersedes Wave 1 exclusions only for the explicitly authorized capability.

## Do not do these things

- Expand beyond the current owner-approved execution packet. Unless that packet explicitly authorizes an item, do not add Plaid, Actual Budget, bank connectors, Amazon/email ingestion, correction UI, transaction matching, analytics, SwiftUI, Android, multi-user, rental itemization, event streaming, Kubernetes, Redis, or another future feature.
- Commit secrets, signed URLs, auth tokens, or real credentials.
- Commit real receipt images, extracted real-receipt content, or owner personal data.
- Emit real GCP project IDs, Firebase project IDs, or Cloud SQL instance names in public artifacts.
- Use `float` or `Decimal` binary types for currency totals.
- Mark a task complete without the required acceptance evidence.
- Change `contracts/openapi.yaml`, `contracts/extraction-result.schema.json`, or existing Alembic migrations without supervisor approval.
- Run destructive cloud commands without explicit owner authorization in this session.

---

## Working style

- Read relevant existing files before making any change.
- Propose the smallest implementation that satisfies the approved outcome.
- Prefer editing existing files over creating new ones.
- Extend before replacing.
- When changing multiple files: explain what, why, and the smallest safe path.
- When uncertain about a business rule: stop and ask rather than guess.

---

## AI cost guidance

| Task | Model |
|---|---|
| Standard implementation, editing, tests | claude-sonnet-4-6 (current session default) |
| Architecture decisions, irreversible choices, security ambiguity | Escalate to Opus |
| Quick lookup, short factual question | Haiku acceptable |

Keep this file concise — long always-loaded files cost tokens every turn.
