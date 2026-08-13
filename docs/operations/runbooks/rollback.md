# Runbook: Application Rollback

**Triggers:** Broken deploy, regression in /health/ready, rising error rate.
**Controls:** OPS-03, CICD-03.

---

## 1. Traffic rollback (fastest path — seconds)

Redirect traffic to the previous revision without redeploying:

```bash
# Identify the previous good revision:
gcloud run revisions list \
  --service=financial-os-ENVIRONMENT-api \
  --region=REGION \
  --project=PROJECT_ID \
  --format="table(metadata.name, metadata.creationTimestamp, traffic)" \
  --sort-by="~metadata.creationTimestamp" \
  --limit=5

# Roll back to a specific previous revision:
PREV_REVISION="financial-os-ENVIRONMENT-api-XXXXXX"

gcloud run services update-traffic \
  financial-os-ENVIRONMENT-api \
  --region=REGION \
  --to-revisions="${PREV_REVISION}=100" \
  --project=PROJECT_ID

# Do the same for the worker:
PREV_WORKER_REVISION="financial-os-ENVIRONMENT-worker-XXXXXX"

gcloud run services update-traffic \
  financial-os-ENVIRONMENT-worker \
  --region=REGION \
  --to-revisions="${PREV_WORKER_REVISION}=100" \
  --project=PROJECT_ID
```

Verify health after rollback:

```bash
API_URL=$(gcloud run services describe financial-os-ENVIRONMENT-api \
  --region=REGION --project=PROJECT_ID --format="value(status.url)")

curl -sf "${API_URL}/health/ready" | jq .
```

---

## 2. Firebase Hosting rollback

```bash
# List recent releases:
firebase hosting:releases:list --project=FIREBASE_PROJECT_ID

# Roll back to a previous release:
RELEASE_ID="XXXXXXXX"
firebase hosting:rollback "$RELEASE_ID" --project=FIREBASE_PROJECT_ID
```

---

## 3. Database migration rollback

**Only if the broken revision introduced a new migration.** Schema rollbacks are
high-risk; coordinate with the supervisor.

```bash
# Downgrade one migration step:
DATABASE_URL="postgresql+asyncpg://..." alembic downgrade -1

# Verify current schema version:
DATABASE_URL="postgresql+asyncpg://..." alembic current
```

Never downgrade past a migration that has already processed production data
without first verifying that data integrity is preserved.

---

## 4. Pause queue during rollback investigation

If the worker revision is broken and retrying tasks could cause harm:

```bash
gcloud tasks queues pause receipt-processing \
  --location=REGION --project=PROJECT_ID

# Resume after deploying a working revision:
gcloud tasks queues resume receipt-processing \
  --location=REGION --project=PROJECT_ID
```

---

## 5. Root cause and evidence

Document: broken revision SHA and digest, symptom observed, rollback action taken,
time to resolution, and whether any acknowledged receipt was lost during the window.
File an issue before re-enabling the broken feature.
