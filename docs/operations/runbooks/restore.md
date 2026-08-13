# Runbook: Database and Storage Restore

**Triggers:** Data loss, corruption, failed migration, REL-001 invariant alert.
**Controls:** DB-03, OBJ-04, OPS-03, REL-001.
**Severity:** P0 if acknowledged receipts may be lost.

---

## 0. Stop destructive operations first

Before restoring: pause the Cloud Tasks queue and reconciliation scheduler
to prevent concurrent writes during restore:

```bash
# Pause Cloud Tasks queue:
gcloud tasks queues pause receipt-processing \
  --location=REGION \
  --project=PROJECT_ID

# Pause Cloud Scheduler job:
gcloud scheduler jobs pause financial-os-ENVIRONMENT-reconcile \
  --location=REGION \
  --project=PROJECT_ID
```

---

## 1. Identify the restore point

### Cloud SQL PITR

```bash
# List available backups:
gcloud sql backups list \
  --instance=financial-os-ENVIRONMENT \
  --project=PROJECT_ID

# Point-in-time recovery: identify the target timestamp (UTC).
# Use the time just before the corruption or data loss event.
TARGET_TIMESTAMP="2026-08-12T14:00:00Z"
```

### GCS object versioning

```bash
# List all versions of a specific object:
gcloud storage objects list \
  "gs://BUCKET_NAME/originals/RECEIPT_ID/" \
  --all-versions \
  --format="table(name,generation,timeCreated)"

# Restore a specific object version by copying it:
gcloud storage cp \
  "gs://BUCKET_NAME/originals/RECEIPT_ID/image-1.jpg#GENERATION" \
  "gs://BUCKET_NAME/originals/RECEIPT_ID/image-1.jpg"
```

---

## 2. Restore into an isolated target (DO NOT restore directly to production)

```bash
# Clone the production Cloud SQL instance to an isolated restore instance:
gcloud sql instances clone financial-os-ENVIRONMENT \
  financial-os-restore-$(date +%Y%m%d%H%M) \
  --point-in-time="$TARGET_TIMESTAMP" \
  --project=PROJECT_ID

# Connect to the restore instance and verify data:
gcloud sql connect financial-os-restore-TIMESTAMP \
  --user=postgres \
  --project=PROJECT_ID
```

Verification queries (run against isolated restore):

```sql
-- Count receipts by state.
SELECT processing_status, COUNT(*) FROM receipts GROUP BY processing_status;

-- Check for any acknowledged receipts with missing evidence.
SELECT r.id, r.processing_status, COUNT(a.id) as asset_count
FROM receipts r
LEFT JOIN receipt_assets a ON a.receipt_id = r.id AND a.upload_status = 'verified'
WHERE r.processing_status NOT IN ('reserved', 'uploading')
GROUP BY r.id, r.processing_status
HAVING COUNT(a.id) = 0;

-- Verify relational integrity: every verified asset should have a storage_generation.
SELECT COUNT(*) as missing_generation
FROM receipt_assets
WHERE upload_status = 'verified' AND (storage_generation IS NULL OR sha256 IS NULL);
```

---

## 3. Verify GCS object references

```bash
# For each verified asset, confirm the object exists at the recorded generation:
# (Run this script against the isolated restore instance data)
python3 scripts/verify-storage-references.py \
  --db-url="postgresql://..." \
  --bucket="BUCKET_NAME" \
  --report-only
```

---

## 4. Cut over (owner authorization required)

Only after:
- [ ] Restore instance data passes all verification queries
- [ ] GCS object references are confirmed intact
- [ ] Owner explicitly authorizes cutover
- [ ] Zero-loss assertion: all acknowledged receipts accounted for

```bash
# Switch the application to the restore instance by updating the database URL secret.
# Requires a brief maintenance window (stop services, update secret, restart).
```

---

## 5. Resume operations

```bash
gcloud tasks queues resume receipt-processing \
  --location=REGION --project=PROJECT_ID

gcloud scheduler jobs resume financial-os-ENVIRONMENT-reconcile \
  --location=REGION --project=PROJECT_ID
```

---

## 6. Document the incident

Record: trigger, affected receipts, restore point used, verification results,
recovery time, and evidence of zero acknowledged-receipt loss.
