# Wave 1 local verification

**Date:** August 13, 2026
**Scope:** Receipt-capture vertical slice, synthetic data only
**Disposition:** Local implementation verified; cloud release gates remain open

## Verified evidence

| Area | Command or observation | Result |
|---|---|---|
| Backend lint | `ruff check .` | Pass |
| Backend format | `ruff format --check .` | Pass |
| Backend types | `mypy src apps/api alembic` | Pass, 47 source files |
| Unit and contract tests | `pytest tests/unit tests/contract` | Pass, 65 tests |
| PostgreSQL integration | `pytest tests/integration` against isolated PostgreSQL 15 | Pass, 7 tests |
| Migration lifecycle | upgrade, one-revision downgrade, re-upgrade on isolated PostgreSQL 15 | Pass |
| PWA tests | Vitest | Pass, 77 tests |
| PWA types and lint | TypeScript strict check and ESLint | Pass |
| PWA production artifact | Vite PWA build with generated service worker | Pass |
| Infrastructure | Terraform 1.9.8 format and validate | Pass |
| Container | Multi-stage image build | Pass |
| Runtime identity | `id` inside the final image | Non-root `appuser` (UID 1001) |
| Container probes | `/health/live` and `/health/ready` with synthetic local adapters | Both returned `status=ok` |
| Python dependency audit | `pip-audit --local` after remediation | No known vulnerabilities |
| Repository privacy | Staged-file private-data scan and whitespace check | Pass |

The first audit identified vulnerable development-tool versions of `pip` and
`pytest`. The minimum versions were raised, the compatible async test plugin was
installed, and all backend tests were rerun before the clean audit result above.

## Intentionally not claimed

Twenty-four deployed-environment security tests are present but were skipped
locally because no personally owned GCP project, evidence bucket, hosted PWA, or
Cloud Run endpoint exists. A skipped live test is not release evidence.

No application resource or personal financial data was deployed. The following
must complete in the personal project before real receipt capture:

1. Follow `docs/operations/personal-gcp-bootstrap.md` and review both Terraform
   plans before apply.
2. Replace placeholder secrets, bootstrap PostgreSQL privileges, and run the
   one-shot migration job.
3. Run GitHub CI, including Gitleaks, Trivy, dependency audit, contract checks,
   Terraform validation, and container build.
4. Run the deployed negative-auth, CSP/header, private-bucket, signed-URL, and
   generation-binding tests with synthetic fixtures.
5. Complete synthetic end-to-end extraction and real-iPhone Safari/PWA testing.
