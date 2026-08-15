# Receipt deduplication backfill runbook

**Status:** Active after migration `002`
**Owner:** DollarTrace operating lead
**Last reviewed:** August 15, 2026

## Purpose

Classify receipts that existed before deterministic duplicate detection was
enabled. The operation preserves every image and revision, writes only the
deduplication projection and append-only state events, and defaults to a
rollback-only dry run.

## Preconditions

- Deploy the release image only after migration `002` succeeds.
- Run with the same reviewed release image as the API/worker, using an approved
  runtime database identity with DML access and a secret-injected
  `DATABASE_URL`.
- Do not place database credentials, owner identifiers, receipt identifiers,
  fingerprints, merchant content, or amounts in command arguments or logs.
- Confirm the API and worker are healthy before applying the backfill.

## Dry run

Execute inside the approved one-shot runtime:

```bash
python -m financial_os.operations.backfill_dedup --batch-size 50
```

The command prints aggregate counts only. Confirm that:

- the mode is `DRY RUN`;
- the evaluated count is plausible for the existing receipt history;
- only `unique`, `suspected_duplicate`, and `confirmed_duplicate` aggregates
  appear; and
- the command exits successfully without changing any receipt or state event.

For a bounded operational check, add `--limit N`, where `N` is a positive
integer. A limited dry run is diagnostic only and is not an apply substitute.

## Apply

After the dry-run result is accepted, execute:

```bash
python -m financial_os.operations.backfill_dedup --apply --batch-size 50
```

The operation selects only extracted receipts whose status is `unchecked`,
orders them oldest-first, and commits bounded batches. It is safe to resume: an
interrupted rerun skips completed receipts and converges canonical links using
the earliest acknowledged timestamp and UUID tie-break.

## Verification

1. Rerun the dry-run command. The evaluated count should be zero unless new
   unchecked extracted receipts arrived during the operation.
2. Query privacy-safe aggregates only: counts by deduplication status and count
   of confirmed duplicates whose canonical pointer is null or self-referential.
   The invalid-pointer count must be zero.
3. Verify one synthetic or owner-controlled acceptance case through the private
   UI: the canonical receipt remains available and a duplicate is labeled while
   its image and extracted revision remain retrievable.
4. Confirm API/worker health and error-rate baselines remain normal.

## Failure and recovery

- A failed batch rolls back as a transaction. Correct the cause and rerun the
  same command; do not delete receipts or evidence.
- If the classification rule is defective, stop further apply runs, deploy a
  corrected versioned rule, and reclassify through a reviewed repair operation.
  Do not manually rewrite fingerprints or canonical links in production.
- Application rollback does not downgrade migration `002`; the additive columns
  and evidence remain in place. Older application code can ignore them.

## Privacy-safe evidence

Record release commit, job result, start/end time, aggregate counts, and health
checks. Never record individual receipt identifiers, merchants, items, amounts,
fingerprints, database URLs, project identifiers, or screenshots containing
private financial evidence.
