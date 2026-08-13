# Financial OS — Implementation Contracts

**Status:** Wave 1 contract freeze — `planning-baseline-2026-08-12-r1`  
**Date:** August 12, 2026  
**Owner:** Claude implementation supervisor  
**Supersedes:** Any conflicting statement in `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md` or `personal_ai_finance_codex_handoff.md`

This document resolves all mandatory conditions from `docs/reviews/gate-a/synthesis-and-disposition.md` §3 and §4 that require explicit specification. Changes to frozen contracts require supervisor approval, impact analysis, and affected-agent notification.

---

## 1. P-03 — Canonical precedence

**Condition:** State canonical precedence; confirm no Actual Budget / Plaid / rental day-one scope.

### 1.1 Document authority order

| Tier | Document(s) | Authority |
|---|---|---|
| 1 | `docs/security/control-baseline.md` MUST controls | Release blocking; never silently waived |
| 2 | `docs/product/PRD.md`, `docs/product/roadmap.md` | Product scope and outcomes |
| 3 | `docs/architecture/system-architecture.md`, `docs/architecture/data-architecture.md`, `docs/architecture/technology-recommendation.md` | System and data design |
| 4 | `docs/implementation/execution-packets/sprint-0-1-receipt-capture.md`, this document | Implementation specification |
| 5 | `docs/governance/ai-development-operating-model.md` | Process and roles |
| Context only | `MAC_MINI_FINANCIAL_OS_BLUEPRINT.md`, `personal_ai_finance_codex_handoff.md` | Supporting background; superseded by Tiers 1–5 on any conflict |

In any conflict between a tier-6 (context) document and a tier 1–5 document, the tier 1–5 document governs. Agents must stop and report conflicts rather than resolve them silently.

### 1.2 Day-one scope exclusions confirmed

The following are explicitly **not** in Wave 1 scope, regardless of any statement in context-tier documents:

- Plaid or bank API connectors
- Actual Budget integration or any budgeting interface
- Rental property day-one itemization or tenant modeling
- Amazon, email, Costco, statement, or payroll source automation
- Receipt editing, correction, or review UI
- Transaction matching or reconciliation
- Analytics dashboard or spending intelligence
- SwiftUI, Android native application, or local LLM
- Multi-user, sharing, or money movement

Any agent that encounters a context-tier reference to these topics must treat it as future scope only.

---

## 2. A-01 — Concurrent task idempotency and duplicate-delivery response

**Condition:** Specify concurrent task idempotency and the successful duplicate-delivery response.

### 2.1 Receipt create idempotency

**Contract:** Two concurrent `POST /api/v1/receipts` requests with the same `client_submission_key` from the same owner both receive `2xx`. Only one receipt row is created.

**Mechanism:** A `UNIQUE` constraint on `receipts(owner_id, client_submission_id)` with an `ON CONFLICT DO NOTHING` or `INSERT ... ON CONFLICT ... RETURNING` strategy. The first writer wins atomically; the second writer reads the existing row and returns it with fresh upload capabilities.

**Response semantics:**

| Scenario | HTTP status | Body |
|---|---|---|
| First create | 201 Created | New receipt + upload capabilities |
| Duplicate key (receipt exists in any state) | 200 OK | Existing receipt + fresh upload capabilities |

Both callers receive a usable response. The client treats both as success and proceeds to upload.

**Test requirement (A-01):** Send two concurrent `POST /api/v1/receipts` requests with the same `client_submission_key`. Both must return `2xx`. Exactly one receipt row must exist in the database. One current revision must exist per receipt after extraction.

### 2.2 Worker duplicate delivery idempotency

Cloud Tasks may deliver the same task more than once. The worker must be idempotent:

1. **Lease acquisition:** Before any extraction work, the worker attempts to transition the receipt from `queued` → `processing` using an optimistic lock on `receipts.row_version`. If the receipt is already `processing` or in a terminal state, the worker returns `200` with `outcome: "no_op"` without re-running extraction.
2. **Attempt deduplication:** The worker inserts a `processing_attempts` row with a `UNIQUE` constraint on `(receipt_id, pipeline_version, attempt_number)`. A duplicate delivery of the same attempt number returns 200 after finding the existing attempt row.
3. **Revision deduplication:** A new `receipt_revisions` row is inserted only when extraction succeeds and the `asset_manifest_hash` is distinct from any existing revision for this receipt. The `current_revision_id` pointer is updated atomically in the same transaction.

**Guarantee:** Duplicate task delivery cannot create duplicate current revisions or duplicate line-item records.

**Test requirement:** Execute the same `POST /internal/v1/receipts/{id}/process` twice. Exactly one `receipt_revisions` row must exist. `receipts.current_revision_id` must point to exactly one revision.

---

## 3. A-02 — Migration as a one-shot pre-deploy job

**Condition:** Specify migration as a one-shot pre-deploy job/step; services never migrate concurrently at startup.

### 3.1 Deployment sequence

```
CI build → image tagged with immutable digest
  ↓
Migration step: run alembic upgrade head (single Cloud Run Job or CI step)
  Migration exits 0 → proceed
  Migration exits non-zero → deployment halts; no traffic switched
  ↓
Deploy API revision (Cloud Run): --no-traffic initially
  ↓
Deploy worker revision (Cloud Run): --no-traffic initially
  ↓
Smoke test: GET /health/ready → 200 on both revisions
  ↓
Switch traffic to new revisions
```

### 3.2 Invariants

- `alembic upgrade head` is **never** called inside the API or worker application startup code.
- Multiple API/worker replicas may start after the migration step completes — this is safe because the schema is already up-to-date.
- If two deployments race (e.g., a broken CI retry), Alembic's version table prevents double-application of any migration. Migrations must be idempotent or use Alembic's built-in version guard.
- The migration step runs with its own least-privilege Cloud SQL user that has DDL rights. The API and worker runtime roles have DML rights only (DB-01).

### 3.3 Expand-contract migration strategy

- **Additive changes** (new columns nullable, new tables): deploy migration, then update application code.
- **Breaking changes** (column rename, type change): use a two-step expand-contract: add new column, deploy code that writes both, migrate data, remove old column.
- Never deploy a migration that breaks the running application revision before traffic is switched.

**Test requirement:** CI migration validation step runs `alembic upgrade head` against an ephemeral database and `alembic downgrade -1` to verify reversibility.

---

## 4. A-03 — Canonical `asset_manifest_hash` algorithm

**Condition:** Define canonical ordered `asset_manifest_hash` algorithm.

### 4.1 Algorithm

The `asset_manifest_hash` is computed deterministically from the finalized, verified asset set. It identifies the exact evidence presented to the extraction provider for a given run.

**Inputs:** All `receipt_assets` rows for the receipt where `upload_status = 'verified'`, ordered ascending by `ordinal`.

**Algorithm:**

```python
import hashlib, json

def compute_asset_manifest_hash(verified_assets: list[dict]) -> str:
    """
    verified_assets: list of dicts with keys ordinal (int), object_key (str), sha256 (str).
    Must be sorted by ordinal ascending before calling.
    sha256 is the hex-encoded SHA-256 of the asset content, as stored in receipt_assets.sha256.
    """
    entries = sorted(verified_assets, key=lambda a: a["ordinal"])
    manifest_input = json.dumps(
        [
            {
                "ordinal": entry["ordinal"],
                "object_key": entry["object_key"],
                "sha256": entry["sha256"],
            }
            for entry in entries
        ],
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(manifest_input.encode("utf-8")).hexdigest()
```

**Key properties:**

- **Deterministic:** same inputs always produce the same hash.
- **Order-sensitive:** ordinal determines sort order; a receipt with images A, B produces a different hash from B, A.
- **Content-sensitive:** `sha256` captures the actual image bytes, not just the object name.
- **Cross-path consistent:** direct upload, retry, and worker paths all produce the same hash for the same evidence set.
- **Cross-language consistent:** the JSON serialization is specified exactly (no whitespace, sorted keys) so a TypeScript or Go implementation produces identical output.

### 4.2 Storage

Stored in `extraction_runs.asset_manifest_hash` for every run. Two runs with the same `asset_manifest_hash` on the same receipt represent identical evidence presented to the provider (modulo prompt/model differences captured by `prompt_version`/`model_id`).

**Test requirement:** Compute the hash from three independent code paths (direct upload path, retry path, worker path) for the same synthetic evidence set. All three must produce identical hex strings.

---

## 5. S-01 — Immutable GCS object generation binding

**Condition:** Bind finalized/processed evidence to immutable GCS object generation and content hash so signed-URL overwrite cannot substitute evidence.

### 5.1 Finalization binding

When `POST /api/v1/receipts/{id}/finalize` verifies an uploaded object (OBJ-03), the API:

1. Calls the GCS Objects.get metadata API to retrieve the object's `generation` number and `md5Hash` / `crc32c`.
2. Stores `generation` in `receipt_assets.storage_generation` and the server-observed SHA-256 in `receipt_assets.sha256`.
3. Marks the asset `upload_status = 'verified'` in the same database transaction.

After this point, the `object_key` + `storage_generation` pair identifies a single immutable, byte-for-byte specific GCS object version.

### 5.2 Worker evidence read

When the worker reads assets for extraction:

1. Fetches each object by `object_key` **with generation pinning**: `storage.bucket(bucket).blob(key, generation=generation)`.
2. Verifies the fetched object's SHA-256 matches `receipt_assets.sha256`.
3. Any mismatch → log a `GENERATION_MISMATCH` error event → mark the attempt `terminal_failed` (not retryable, because the original evidence is no longer accessible at that generation).

### 5.3 Download capabilities

Download URLs returned by `POST /api/v1/receipts/{id}/assets/{asset_id}/download` must include the `generation` parameter so the URL retrieves the exact verified version and cannot be used to access a later overwritten version of the same object name.

### 5.4 Overwrite protection

Evidence buckets are configured with uniform bucket-level access and public access prevention (OBJ-01). Object versioning is enabled. Original evidence objects (`originals/` prefix) must not be deletable by any runtime service account; only a named recovery role may delete them, and only with owner authorization.

**Test requirement (S-01 negative test):** Upload object O at generation 1 and finalize. Replace O with different content (generation 2). Trigger worker processing. Worker must detect the generation mismatch and mark the attempt `terminal_failed` without promoting the substituted content to a revision.

---

## 6. S-02 — Firebase-compatible CSP without `unsafe-inline` or `unsafe-eval`

**Condition:** Freeze and test a Firebase-compatible CSP with no `unsafe-inline` or `unsafe-eval`.

### 6.1 Frozen CSP directives

The following CSP is frozen for the Firebase Hosting deployment. Exact origins are verified during implementation preflight and recorded as an ADR if changes are required.

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self'
    https://www.gstatic.com
    https://apis.google.com;
  style-src 'self'
    https://fonts.googleapis.com;
  font-src 'self'
    https://fonts.gstatic.com;
  connect-src 'self'
    https://*.googleapis.com
    https://identitytoolkit.googleapis.com
    https://securetoken.googleapis.com
    https://firebaseinstallations.googleapis.com;
  img-src 'self' data: blob:;
  media-src blob:;
  frame-src 'self' https://accounts.google.com;
  frame-ancestors 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
```

**No `unsafe-inline`. No `unsafe-eval`.** The Vite build must produce no inline scripts. Any hashed inline script (e.g., service-worker registration) must use a `'sha256-...'` hash source rather than `unsafe-inline`.

Additional headers required (APP-03, NET-01):

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Permissions-Policy: camera=(self), microphone=(), geolocation=(), payment=()
```

### 6.2 Verification requirements

1. Deploy to Firebase Hosting (staging or production).
2. Fetch the deployed `index.html` and assert all headers above are present and match the frozen values.
3. Run a stored-XSS fixture test: inject `<img src=x onerror=alert(1)>` into merchant and line-item fields; assert no script execution occurs and the CSP report-only (if enabled) or browser console shows a CSP violation, not execution.
4. Open browser DevTools → Console and confirm no CSP violations on the normal capture flow.

**Test requirement (S-02):** CI asserts `Content-Security-Policy` header value matches the frozen directives via a deployment smoke test. No `unsafe-inline` or `unsafe-eval` appears in the deployed header.

---

## 7. `crypto.randomUUID()` — client submission key specification

**Context:** Gate A §4 mandatory condition before production release.

### 7.1 Specification

`client_submission_key` is a Version 4 UUID in canonical lowercase form (e.g., `"a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5"`).

**Generation rule:** The client generates the key using `crypto.randomUUID()` from the Web Crypto API **before** the `POST /api/v1/receipts` request is constructed. This is a CSPRNG-backed function available in all modern browsers in secure contexts (HTTPS or localhost).

```typescript
// In the PWA, before building the create-receipt request body:
const clientSubmissionKey = crypto.randomUUID(); // Web Crypto API, CSPRNG-backed
```

**Requirements:**

- The key must be generated fresh for each new receipt. Never reuse a key from a previous receipt.
- The key must never be generated server-side and communicated to the client; the idempotency guarantee depends on the client holding the authoritative key before the first request.
- If `crypto.randomUUID()` throws (unsupported context), the client must surface an error and not proceed. There is no acceptable fallback to `Math.random()` or timestamp-based keys.
- The key must be persisted in client session state for the active receipt draft so that retries of a failed `POST /api/v1/receipts` reuse the same key (idempotency).

### 7.2 Server-side handling

The server stores `client_submission_key` verbatim in `receipts.client_submission_id` without modification. It enforces the `UNIQUE (owner_id, client_submission_id)` constraint. It never generates a key on the client's behalf.

---

## 8. Worker extraction input ceilings

**Context:** Gate A §4 mandatory condition before production release — "worker-side extraction input ceiling and terminal cost circuit breaker."

### 8.1 Input ceiling constants

| Constant | Value | Rationale |
|---|---|---|
| `MAX_ASSETS_PER_EXTRACTION` | 10 | Matches `MAX_ASSETS_PER_RECEIPT` enforced at create time |
| `MAX_ASSET_BYTES` | 10,485,760 (10 MiB) | Per-image limit after EXIF strip; typical iPhone HEIC/JPEG range |

HEIC/HEIF handling is explicit:

- When a browser leaves `File.type` empty, the PWA infers only allowlisted
  image types from a case-insensitive filename extension.
- The MIME type bound into the signed upload URL and the upload
  `Content-Type` header must be identical.
- Evidence verification records the MIME type detected from file magic, not an
  untrusted client declaration.
- Browsers that cannot decode HEIC for local preview show a truthful
  **HEIC photo ready** fallback; lack of preview does not discard the original.
- GCS CORS permits only the two exact Firebase Hosting aliases (`web.app` and
  `firebaseapp.com`) for the deployed project; wildcards remain prohibited.
| `MAX_TOTAL_EXTRACTION_BYTES` | 52,428,800 (50 MiB) | Total bytes across all assets in one extraction call |
| `MAX_PROMPT_TOKENS` | Set after P-01 benchmark | TBD; placeholder until benchmark evidence exists |
| `MAX_EXTRACTION_COST_CENTS` | 50 (USD cents) | Terminal cost circuit breaker per extraction attempt |

These values are read from environment variables (see `.env.example`) and must not be hard-coded in application logic.

### 8.2 Enforcement

Before calling `ReceiptExtractor.extract()`, the worker must:

1. Count verified assets: if `count > MAX_ASSETS_PER_EXTRACTION` → terminal failure with `safe_error_code = "CEILING_ASSET_COUNT"`.
2. Measure each asset's byte size after EXIF strip: if any `> MAX_ASSET_BYTES` → terminal failure with `safe_error_code = "CEILING_ASSET_BYTES"`.
3. Sum all asset bytes: if `total > MAX_TOTAL_EXTRACTION_BYTES` → terminal failure with `safe_error_code = "CEILING_TOTAL_BYTES"`.
4. If the provider returns a cost estimate before submission: if `cost > MAX_EXTRACTION_COST_CENTS` → terminal failure with `safe_error_code = "CEILING_COST"`. If cost is only available post-submission, record and alert; do not retry.

### 8.3 Terminal cost circuit breaker

If a provider call returns a cost that exceeds `MAX_EXTRACTION_COST_CENTS`:

- Mark the extraction attempt `terminal_failed` with `safe_error_code = "COST_CIRCUIT_BREAKER"`.
- Emit a `processing.cost_ceiling_exceeded` structured event with the amount (no receipt content).
- Do not retry automatically. The owner must investigate and either increase the ceiling or reject the receipt.

This control prevents unbounded provider spend from a single malformed or adversarially large receipt.

### 8.4 `MAX_PROMPT_TOKENS` placeholder

`MAX_PROMPT_TOKENS` is set to a placeholder value of `32768` until the P-01 extraction benchmark produces evidence. After the benchmark:

1. Measure the p95 prompt token count across the synthetic benchmark set.
2. Set `MAX_PROMPT_TOKENS` to `max(p95 * 1.5, 8192)` rounded to the nearest 1024.
3. Record the benchmark evidence and the chosen value as a dated entry in `docs/implementation/`.
4. Update `.env.example` and this document.

---

## 9. Summary of Gate A condition resolutions

| Condition ID | Status | Evidence location |
|---|---|---|
| P-03 | Resolved — §1 of this document | This document §1 |
| A-01 | Resolved — §2 of this document | Concurrent duplicate test: `tests/integration/receipts/test_create_idempotency*` |
| A-02 | Resolved — §3 of this document | Migration/deploy contract: `.github/workflows/`, `alembic/` |
| A-03 | Resolved — §4 of this document | Cross-path hash tests: `tests/unit/domain/test_asset_manifest_hash*` |
| S-01 | Resolved — §5 of this document | Replacement/replay negative test: `tests/integration/storage/test_generation_binding*` |
| S-02 | Resolved — §6 of this document | Deployed header assertion: `tests/security/test_csp_headers*` |
| `crypto.randomUUID` | Resolved — §7 of this document | PWA implementation: `apps/web/src/receipts/` |
| Worker input ceilings | Resolved — §8 of this document | Worker unit tests: `tests/unit/domain/test_worker_ceilings*` |

Conditions P-01, P-02, and A-04 require empirical evidence (benchmark, real-iPhone spike, cold-start measurement) and are not resolvable by specification. They are tracked as open items and must be completed before Wave 1 parallel build launches.
