# Runbook: Secret or Credential Leak

**Triggers:** Credential found in repository, log, CI artifact, or public channel.
**Controls:** OPS-03, CICD-01.
**Severity:** P0 if the leaked credential is currently valid.

---

## 1. Determine what leaked

| Credential type | Immediate risk | Action |
|---|---|---|
| Firebase API key | Low (public-safe, auth still enforced) | Rotate; audit auth logs |
| GCP service account key | High | Disable immediately → step 2 |
| WIF binding / OIDC token | Time-limited | Check expiry; disable pool provider if needed |
| Signed GCS URL | Medium (short expiry) | See object exposure sub-runbook |
| Database URL with password | Critical | Rotate password; revoke all sessions |
| Secret Manager secret value | Depends on secret | Rotate and disable old version |

## 2. Disable the leaked credential immediately

```bash
# Service account key (if a key file was ever created — it must not exist):
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=SA_EMAIL \
  --project=PROJECT_ID

# WIF pool provider (disable to stop all GitHub Actions federation):
gcloud iam workload-identity-pools providers update-oidc \
  github-actions-provider \
  --location=global \
  --workload-identity-pool=github-actions-pool \
  --disabled \
  --project=PROJECT_ID

# Secret Manager version (disable, not delete, to preserve audit trail):
gcloud secrets versions disable VERSION_ID \
  --secret=SECRET_ID \
  --project=PROJECT_ID
```

## 3. Rotate the leaked credential

```bash
# Rotate a Secret Manager secret value:
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_ID \
  --data-file=- \
  --project=PROJECT_ID
```

For Firebase API keys: rotate in the Firebase Console → Project settings → Web API key → Regenerate.

## 4. Remove from source / artifact

If the secret is in a git commit:
1. Do NOT force-push public main branch history — escalate to owner.
2. Rotate immediately (the public view is permanent; rotation limits damage).
3. Open a private security advisory if the repository is public.

## 5. Audit

```bash
# Check recent Cloud Run deployments for unauthorized revisions:
gcloud run revisions list \
  --service=financial-os-ENVIRONMENT-api \
  --region=REGION \
  --project=PROJECT_ID \
  --format="table(metadata.name, metadata.creationTimestamp, spec.serviceAccountName)"

# Check Cloud Storage access logs:
gcloud logging read \
  'resource.type="gcs_bucket" AND protoPayload.methodName=("storage.objects.get" OR "storage.objects.list")' \
  --project=PROJECT_ID \
  --freshness=24h
```

## 6. Notify owner and document

Record: credential type, exposure window, accessed resources (if determinable),
actions taken, rotation evidence, and prevention changes.
