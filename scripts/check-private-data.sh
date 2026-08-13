#!/usr/bin/env bash
# Scan for private data and forbidden patterns in tracked files.
# Runs in CI (CICD-02, OPS-02). Exits non-zero on any match.
set -euo pipefail

ERRORS=0
STAGED_ONLY="${STAGED_ONLY:-false}"

if [[ "$STAGED_ONLY" == "true" ]]; then
  FILES=$(git diff --cached --name-only --diff-filter=ACMR \
    | grep -v '^scripts/check-private-data.sh$' || true)
else
  # All tracked files (exclude binaries, .git, vendor dirs).
  FILES=$(git ls-files \
    | grep -v '^scripts/check-private-data.sh$' \
    | grep -vE '\.(png|jpg|jpeg|gif|ico|woff|woff2|ttf|pdf|zip|tar|gz|bin)$' || true)
fi

if [[ -z "$FILES" ]]; then
  echo "No files to scan."
  exit 0
fi

check_pattern() {
  local description="$1"
  local pattern="$2"
  local allowed_pattern="${3:-}"
  local matches
  matches=""
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ -n "$allowed_pattern" ]]; then
      if grep -E "$pattern" "$file" 2>/dev/null \
        | grep -Ev "$allowed_pattern" \
        | grep -q .; then
        matches+="${file}"$'\n'
      fi
    elif grep -qE "$pattern" "$file" 2>/dev/null; then
      matches+="${file}"$'\n'
    fi
  done <<< "$FILES"
  if [[ -n "$matches" ]]; then
    echo "ERROR: $description pattern found in:"
    printf '%s' "$matches" | sed 's/^/  /'
    ERRORS=$((ERRORS + 1))
  fi
}

# Real GCP project ID pattern (projects/PROJECT_ID or gcp-project-id: PROJECT_ID).
# Allow placeholder values used in examples.
check_pattern \
  "Potential real GCP project ID (non-placeholder)" \
  'projects/[A-Za-z][A-Za-z0-9-]{4,28}[A-Za-z0-9]' \
  'projects/(your-gcp-project-id|your-dev-gcp-project-id|PLACEHOLDER|PROJECT)'

# Firebase project IDs in real form.
check_pattern \
  "Potential real Firebase project ID" \
  '"firebaseProjectId":[[:space:]]*"[a-z][a-z0-9-]{4,28}[a-z0-9]"' \
  '"firebaseProjectId":[[:space:]]*"(your-|PLACEHOLDER)'

# Service account key JSON fragments.
check_pattern \
  "Service account private key material" \
  '"private_key":|"private_key_id":|BEGIN RSA PRIVATE KEY|BEGIN EC PRIVATE KEY'

# Auth tokens or bearer credentials.
check_pattern \
  "Bearer token or auth credential" \
  'Authorization:\s*Bearer\s+[A-Za-z0-9._\-]{20,}|ya29\.[A-Za-z0-9._\-]{20,}'

# Signed GCS URLs.
check_pattern \
  "Signed GCS URL (X-Goog-Signature or X-Amz-Signature)" \
  'X-Goog-Signature=|X-Amz-Signature='

# Database passwords in connection strings.
check_pattern \
  "Database password in connection string (non-placeholder)" \
  'postgresql\+asyncpg://[^/@:]+:[^/@]{8,}@[^/[:space:]]+' \
  ':(changeme|test-only-not-production)@|@(localhost|127\.0\.0\.1)(:|/)'

# Real email addresses in allowlist config (not test fixtures).
check_pattern \
  "Real email in owner allowlist (use subject ID instead)" \
  'OWNER_ALLOWLIST=.*@' \
  '@(example\.com|test\.invalid)'

# Cloud SQL instance connection names with real project.
check_pattern \
  "Real Cloud SQL instance connection name" \
  'CLOUD_SQL_INSTANCE_CONNECTION_NAME=[a-z][a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]+'

if [[ "$ERRORS" -gt 0 ]]; then
  echo ""
  echo "FAIL: $ERRORS private-data pattern(s) detected. See AGENTS.md §7 for prohibited content."
  exit 1
fi

echo "PASS: No private-data patterns detected."
