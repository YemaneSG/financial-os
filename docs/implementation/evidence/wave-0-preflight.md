# Financial OS — Wave 0 Preflight Evidence

**Status:** In progress
**Date:** August 12, 2026
**Environment:** Authorized corporate GCP development project; identifiers intentionally omitted

## Environment

| Check | Result |
|---|---|
| Claude Code | Authenticated through Vertex AI |
| GCP authority | Active corporate identity has project Owner role |
| Required APIs | Vertex AI, Artifact Registry, Cloud Build, IAM Credentials, Cloud Run, Secret Manager, Cloud SQL Admin, Cloud Storage, Cloud Tasks, Cloud Scheduler, Firebase/Hosting, Identity Toolkit, IAM, STS, Resource Manager, and Service Usage enabled |
| Repository | Local Git repository initialized; planning/contract baseline committed at `7ceef90` |
| Bundled runtimes | Node.js, pnpm, Python, and Git available through the Codex workspace runtime |

No real account, project, bucket, database, or Firebase identifiers are recorded in repository artifacts.

## Vertex extraction smoke benchmark

**Model:** `gemini-2.5-flash`
**Region class:** United States Vertex regional endpoint
**Input:** Synthetic PNG receipt containing four grocery lines, weighted quantity, date, subtotal, tax, total, and a masked payment hint
**Controls:** Temperature zero; structured response schema; prompt states that document text is untrusted data; no tools or retrieval

### Expected facts

- Merchant: `LONE STAR MARKET`
- Date: `2026-08-12`
- Line totals: 124, 379, 449, and 1299 minor units
- Subtotal: 2251 minor units
- Tax: 186 minor units
- Total: 2437 minor units

### Observed result

| Measurement | Result |
|---|---|
| API/model access | Pass |
| JSON response-schema adherence | Pass |
| Required fields present | Pass |
| Merchant/date | Exact |
| Line-item count | 4/4 |
| Line totals | 4/4 exact |
| Subtotal/tax/total | Exact |
| Deterministic arithmetic | `2251 + 186 = 2437`, pass |
| Prompt tokens | 1,384 |
| Candidate tokens | 252 |
| Total tokens reported | 2,092, including model reasoning metadata |

### Decision

The exact provider path and structured-extraction mechanism are viable for implementation. Pin `gemini-2.5-flash` for the initial adapter and preserve model/config provenance per extraction.

This single-fixture run is a smoke gate, not an accuracy claim. Field-accuracy targets remain gated on the approved private/synthetic varied evaluation set. Release testing must add multiple merchants, long/multi-image receipts, discounts, tips, weighted items, low contrast, and malformed/adversarial fixtures.

## Remaining physical-device preflight

- Real iPhone Home Screen installation and session persistence
- Camera-produced JPEG/HEIC behavior
- Photo-library HEIC behavior and selected conversion policy
- Signed upload on Wi-Fi and cellular
- End-to-end ten-second acknowledgement measurement

These require the owner's physical iPhone after deployment and are Gate C acceptance items. Implementation preserves both camera and library paths and must fail truthfully if conversion is unsupported.
