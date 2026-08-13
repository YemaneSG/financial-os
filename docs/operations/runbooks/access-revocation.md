# Runbook: Access Revocation

**Triggers:** Lost/stolen phone, suspected session theft, allowlist change needed.
**Controls:** IAM-01, IAM-02, OPS-03.
**Severity:** P1 — act within minutes if active intrusion is suspected.

---

## 1. Revoke application session (fastest path)

Increment the session version in Secret Manager. All existing sessions fail
on their next API call without needing Firebase revocation.

```bash
# Increment the session version secret.
# Replace PROJECT_ID and ENVIRONMENT with actual values.
CURRENT=$(gcloud secrets versions access latest \
  --secret="financial-os-ENVIRONMENT-session-version" \
  --project="PROJECT_ID")

NEW=$((CURRENT + 1))

echo -n "$NEW" | gcloud secrets versions add \
  "financial-os-ENVIRONMENT-session-version" \
  --data-file=- \
  --project="PROJECT_ID"

echo "Session version incremented to $NEW. All existing sessions are now invalid."
```

## 2. Revoke Firebase / Google refresh tokens

If the session version bump is not sufficient or the attack vector is at the
Google identity level:

```bash
# List sessions for the owner identity (Firebase Admin SDK or Console).
# Console path: Firebase Console → Authentication → Users → [owner UID] → Revoke sessions

# CLI (requires Firebase Admin SDK configured):
# firebase auth:revoke-refresh-tokens USER_UID --project FIREBASE_PROJECT_ID
```

Or in the Firebase Console:
1. Navigate to **Authentication → Users**.
2. Find the owner account.
3. Click **Revoke refresh tokens**.

## 3. Remove from allowlist (if identity is compromised)

```bash
# Set the allowlist to empty to prevent ALL access.
echo -n "" | gcloud secrets versions add \
  "financial-os-ENVIRONMENT-owner-allowlist" \
  --data-file=- \
  --project="PROJECT_ID"
```

To restore access, add the new/verified subject ID:

```bash
echo -n "google:NEW_SUBJECT_ID" | gcloud secrets versions add \
  "financial-os-ENVIRONMENT-owner-allowlist" \
  --data-file=- \
  --project="PROJECT_ID"
```

## 4. Review audit logs

```bash
# Review authorization events from the suspected time window.
gcloud logging read \
  'jsonPayload.event=("auth.success" OR "auth.failure" OR "auth.forbidden") AND resource.type="cloud_run_revision"' \
  --project="PROJECT_ID" \
  --freshness=24h \
  --format="table(timestamp, jsonPayload.event, jsonPayload.receipt_id)"
```

## 5. Re-enable access

1. Verify owner identity and device posture.
2. Restore allowlist with verified subject ID (step 3 above).
3. Confirm the new session works (GET /api/v1/receipts → 200).
4. Document the incident timeline and close.
