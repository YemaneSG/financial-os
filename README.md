# Financial OS

A private, single-owner financial data application. Captures receipt photos from an installable iPhone PWA, processes them through a structured extraction pipeline, and produces durable, auditable financial records.

This repository is a public portfolio case study in production-minded single-user financial software. All fixtures, screenshots, and CI artifacts use synthetic data. No real receipts, financial records, or personal identifiers are committed here.

---

## What it does

1. **Capture** — Install the PWA on iPhone. Photograph one or more receipt images.
2. **Upload** — Images upload directly to private object storage via short-lived server-issued capabilities.
3. **Acknowledge** — Server verifies the evidence set and durably records the receipt before returning "saved."
4. **Extract** — A private worker asynchronously calls a multimodal AI provider, validates the structured output, and promotes it to an immutable revision.
5. **Review** — The PWA shows processing status, structured line-item data, and validation findings.

---

## Architecture overview

```
iPhone PWA (Firebase Hosting)
  ↓ Bearer JWT
Public API (Cloud Run)
  ↓ signed capability
Private evidence bucket (Cloud Storage)
  ↓ queue task (OIDC)
Processing worker (Cloud Run, private)
  ↓ provider interface
Vertex AI multimodal adapter
  ↓
PostgreSQL (Cloud SQL)
```

The API and worker are two deployment processes from one Python codebase (`src/financial_os/`). The frontend is a React/TypeScript PWA in `apps/web/`. Domain logic has no dependency on any cloud SDK or web framework.

Full system design: [`docs/architecture/system-architecture.md`](docs/architecture/system-architecture.md)  
Data model: [`docs/architecture/data-architecture.md`](docs/architecture/data-architecture.md)  
API contract: [`contracts/openapi.yaml`](contracts/openapi.yaml)

---

## Repository layout

```
apps/
  web/                   # React/TypeScript/Vite PWA
  api/                   # FastAPI entry point (public API)

src/financial_os/
  domain/                # values, states, errors, invariants
  models/                # SQLAlchemy persistence models
  services/              # receipt and worker use cases
  schemas/               # HTTP and extraction schemas
  adapters/              # auth, database, extraction, queue, storage, observability
  auth/                  # owner JWT and internal OIDC verification
  routers/               # public API, health, and private worker routes
  config.py              # validated environment configuration

tests/
  unit/
  integration/
  contract/
  e2e/
  fixtures/synthetic/    # synthetic receipts and responses only

infra/                   # Terraform modules and environments
contracts/               # frozen OpenAPI and JSON Schema
docs/                    # architecture, security, governance, product
alembic/                 # database migrations
.github/workflows/       # CI/CD
```

---

## Development setup

Prerequisites: Python 3.12+, Node 20+, Docker (for local Postgres).

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Database migrations (after Postgres is running)
alembic upgrade head

# Frontend (from the repository root)
corepack enable
pnpm install --frozen-lockfile
pnpm dev

# API (development)
uvicorn apps.api.main:app --reload
```

Copy `.env.example` to `.env` and fill in the required values. Never commit `.env`.

Personal cloud setup: [`docs/operations/personal-gcp-bootstrap.md`](docs/operations/personal-gcp-bootstrap.md)

---

## API

The versioned API is documented in [`contracts/openapi.yaml`](contracts/openapi.yaml).

All private routes require a Firebase-issued Bearer token for the allowlisted owner identity. Internal worker routes accept only Cloud Tasks OIDC-authenticated requests.

Base path: `/api/v1/` (public), `/internal/v1/` (worker-only), `/health/` (probe).

---

## Security and privacy

- No real financial data in this repository.
- No public access to evidence storage; all retrieval uses server-authorized short-lived capabilities.
- No long-lived service-account keys; CI uses Workload Identity Federation.
- Content Security Policy covers Firebase Auth origins without `unsafe-inline` or `unsafe-eval`.
- Full control baseline: [`docs/security/control-baseline.md`](docs/security/control-baseline.md)

---

## Governance

Development uses a formal AI-assisted operating model with bounded execution packets, independent review gates, and evidence-backed acceptance criteria.

- Operating model: [`docs/governance/ai-development-operating-model.md`](docs/governance/ai-development-operating-model.md)
- Agent contributor guide: [`AGENTS.md`](AGENTS.md)
- Requirements traceability: [`docs/product/requirements-traceability.md`](docs/product/requirements-traceability.md)

---

## Status

**Wave 0 / Wave 1 — platform preflight and contract implementation.**  
Gate A approved with conditions on August 12, 2026. See [`docs/reviews/gate-a/synthesis-and-disposition.md`](docs/reviews/gate-a/synthesis-and-disposition.md).

Production release is gated on the conditions listed in that document. Private data, production deployments, and destructive cloud changes are not authorized by this repository state alone.
