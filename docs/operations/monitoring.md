# Operations: Monitoring and Alerting

**Controls:** OPS-01, LOG-01, LOG-02.

---

## Dashboards and metrics

All metrics flow to Cloud Monitoring via structured Cloud Run logs and log-based metrics.

### Key metrics

| Metric | Normal range | Alert threshold |
|---|---|---|
| `financial_os/acknowledged_receipts_total` | Growing | REL-001 alert if it stops while uploads are occurring |
| `financial_os/processing_terminal_failures_total` | Near 0 | > 5 in 10 minutes → WARNING |
| `financial_os/invariant_violation_rel001_total` | Always 0 | Any value > 0 → CRITICAL (P0) |
| `financial_os/cost_ceiling_exceeded_total` | Near 0 | Any value > 0 → WARNING |
| Cloud Run request latency (p99) | < 5s | > 10s → WARNING |
| Cloud Run error rate (5xx) | < 1% | > 5% → WARNING |
| Cloud SQL connections | < 80% of max | > 90% → WARNING |

### Uptime checks

| Check | Interval | Alert if failing for |
|---|---|---|
| API liveness (`/health/live`) | 60s | 2 minutes |
| API readiness (`/health/ready`) | 5 minutes | 10 minutes |

---

## Alert response

### REL-001 violation (P0)

1. Stop reconciliation and queue immediately (see `runbooks/restore.md` step 0).
2. Compare receipt table, processing_attempts, and GCS inventory.
3. Do NOT delete or overwrite any evidence until root cause is established.
4. Follow restore runbook.

### API liveness failure

1. Check Cloud Run service health in the console.
2. Check Cloud Run logs for startup errors.
3. Verify Cloud SQL connectivity from the service.
4. Roll back if a recent deploy coincides (see `runbooks/rollback.md`).

### High terminal failure rate

1. Check `safe_error_code` in processing failure logs to identify the pattern.
2. Common causes: CEILING_ASSET_BYTES (large images), SCHEMA_VALIDATION_FAILED (model drift).
3. For CEILING_* codes: review `.env.example` ceiling constants; adjust only after evidence.
4. For SCHEMA_VALIDATION_FAILED: check model output; may require prompt/schema update.

### Cost circuit breaker

1. Check `processing.cost_ceiling_exceeded` log event for the affected receipt ID.
2. Do NOT retry automatically. Owner must investigate and authorize.
3. Consider increasing `WORKER_MAX_EXTRACTION_COST_CENTS` in Secret Manager if the ceiling
   is too conservative; document the evidence.

---

## Log queries (Cloud Logging)

```bash
# All structured financial-os events in the last hour:
gcloud logging read \
  'jsonPayload.service="financial-os-api" OR jsonPayload.service="financial-os-worker"' \
  --project=PROJECT_ID \
  --freshness=1h \
  --format="table(timestamp, jsonPayload.event, jsonPayload.receipt_id, jsonPayload.outcome)"

# Processing failures with safe error codes:
gcloud logging read \
  'jsonPayload.event="processing.failed"' \
  --project=PROJECT_ID \
  --freshness=24h \
  --format="table(timestamp, jsonPayload.receipt_id, jsonPayload.safe_error_code)"

# REL-001 invariant events:
gcloud logging read \
  'jsonPayload.invariant="REL-001"' \
  --project=PROJECT_ID \
  --freshness=7d
```

---

## Budget monitoring

The billing budget alert fires at 50%, 90%, and 100% of the monthly limit (default $50/month).
Alerts go to the configured email and to GCP billing contacts.

To adjust the budget:
```bash
# Update the monthly budget amount in Terraform:
# infra/environments/dev/terraform.tfvars → monthly_budget_usd = NEW_VALUE
# Then: terraform apply
```

---

## Restore smoke test evidence (DB-03)

Before calling production ready, run and record:

```bash
# 1. List Cloud SQL automated backups:
gcloud sql backups list \
  --instance=financial-os-ENVIRONMENT \
  --project=PROJECT_ID

# 2. Clone to isolated instance and verify row counts match:
gcloud sql instances clone financial-os-ENVIRONMENT financial-os-restore-test \
  --project=PROJECT_ID

# 3. Run verification queries against the clone (see restore runbook).
# 4. Delete the clone after verification.

gcloud sql instances delete financial-os-restore-test \
  --project=PROJECT_ID --quiet
```

Record the date, backup timestamp used, row counts, and pass/fail for all
verification queries in `docs/implementation/restore-smoke-test-record.md`.
