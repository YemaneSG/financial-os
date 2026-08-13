# Production bootstrap evidence — August 13, 2026

**Status:** Cloud deployment complete; owner iPhone acceptance pending
**Environment:** Personally controlled GCP project; private identifiers intentionally omitted

## Session objective

Deploy the approved Wave 1 receipt-capture vertical slice so the owner can install
the iPhone PWA, authenticate, submit ordered receipt images, receive a truthful
durable acknowledgement, and retrieve structured data or an explicit
failure/review state.

## Constraints and non-goals

- Preserve owner-only access, private evidence storage, durable-before-acknowledge
  semantics, authenticated worker invocation, deterministic validation, and the
  no-tools extraction boundary.
- Use the existing managed GCP modular-monolith architecture and one-shot database
  migration path.
- Do not add Plaid, bank ingestion, Amazon/email ingestion, transaction matching,
  analytics, rental itemization, BioStack integration, or Mac Mini services.
- Keep deployment identifiers, credentials, owner identity values, and real
  financial content outside tracked files and public evidence.

## Release evidence

- **Pass:** Infrastructure is applied in the personally controlled project; the
  final Terraform plan reports no changes.
- **Pass:** Runtime values are held in Secret Manager and no owner identifier,
  credential, deployment identifier, or real financial content is tracked.
- **Pass:** Passwordless Cloud SQL roles, committed Alembic migration, and the
  single-owner authorization row completed through private one-shot jobs.
- **Pass:** API liveness/readiness return 200; readiness confirms database,
  storage, and queue dependencies.
- **Pass:** Production API documentation is disabled (404), unauthenticated
  receipt access is denied (401), and the private worker cannot be invoked
  directly (404).
- **Pass:** Firebase Hosting serves the PWA, all required security headers pass,
  and the same-origin API rewrite preserves the authentication boundary.
- **Pass:** Exactly one Firebase user exists. The authenticated owner completed
  a live browser-to-API-to-Cloud-SQL receipt-list round trip.
- **Pass:** Cloud SQL automated backups/PITR and evidence-bucket versioning,
  soft-delete, uniform access, and public-access prevention are enabled.
- **Pending Gate C:** Use a non-sensitive test receipt on the owner's real iPhone
  to verify Home Screen install, persistent auth, camera, library fallback,
  signed upload, durable acknowledgement, history/detail, Wi-Fi, and cellular.
- **Pending Sprint 2 operations:** Execute and time the documented restore drill.

## Activity log

| Time (America/Chicago) | Activity | Result |
|---|---|---|
| 2026-08-13 | Owner created a personally controlled billing account and authorized deployment. | Pass |
| 2026-08-13 | Repository state and canonical Wave 1 packet re-read before cloud actions. | Pass |
| 2026-08-13 | Provisioned private network, Cloud SQL, evidence storage, Secret Manager, Artifact Registry, Cloud Tasks, scheduler, Cloud Run services/jobs, Firebase, monitoring, and the USD 50 monthly budget. | Pass |
| 2026-08-13 | Bootstrapped least-privilege IAM database roles and applied the initial schema. Corrected an implicit-transaction defect that previously rolled back a nominally successful migration; final schema commit and idempotent rerun passed. | Pass |
| 2026-08-13 | Registered exactly one Firebase owner and synchronized the stable provider subject to the encrypted allowlist and authorization table. Email is not the authorization key. | Pass |
| 2026-08-13 | Published the installable PWA and changed Google authentication from popup to redirect. Updated CSP for the Firebase auth iframe. | Initial deployment passed; later cross-browser testing exposed a cross-origin redirect-state defect corrected below. |
| 2026-08-13 | Verified live API 200/200 health, 404 production docs, 401 unauthenticated receipts, 404 direct worker, 100% API traffic, restored migration runner, and complete hosting headers. | Pass |
| 2026-08-13 | Verified authenticated owner history query against the deployed API and Cloud SQL; clean first-run result contained zero receipts. | Pass |
| 2026-08-13 | Final Terraform convergence plan. | Pass — no changes |
| 2026-08-13 | Corrected Firebase root caching after an iPhone received the pre-release placeholder. Both hosting domains now return Financial OS with `no-cache, no-store, must-revalidate`; security headers were revalidated. | Pass |
| 2026-08-13 | Diagnosed the first live HEIC attempt: the browser omitted `File.type`, creating a signed-header mismatch, and the `firebaseapp.com` alias was absent from bucket CORS. Deployed extension-based allowlisted MIME inference, exact signed/upload header matching, magic-byte MIME recording, a truthful HEIC preview fallback, retry-state clearing, and both exact Firebase origins. | Pass — 83 PWA tests, 84 backend tests, and live CORS preflights from both origins |
| 2026-08-13 | Reproduced an endless Google sign-in spinner on Safari and Chrome when the app was opened on the `web.app` alias while Firebase redirect state used the `firebaseapp.com` auth domain. Canonicalized the alias before Firebase initialization, removed the app shell and registration script from service-worker precaching, enabled immediate worker activation, and forced worker control files to revalidate. | Pass — lint, type-check, 87 PWA tests, production build, private-data scan, live cache/security headers, and cached-client recovery from `web.app` to the authenticated capture screen with zero browser errors |

## Owner Gate C checklist

Use a clearly non-sensitive test receipt before private financial evidence:

1. Open the deployed `firebaseapp.com` URL in iPhone Safari and sign in with the
   approved Google account.
2. Share → **Add to Home Screen**, launch the installed Financial OS app, close
   it, and reopen it to confirm the session persists.
3. Photograph the test receipt, submit it, and confirm **Receipt saved**.
4. Open **Recent receipts**, then the receipt detail, and confirm either
   structured data or an explicit processing/review/failure state.
5. Repeat using **Choose existing photo**, then repeat one submission on Wi-Fi
   and one on cellular.

Do not interpret a missing durable acknowledgement as success. Keep the source
photo in the iPhone library and retry later, as required by the acquisition
fallback contract.
