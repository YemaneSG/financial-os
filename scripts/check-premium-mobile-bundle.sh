#!/usr/bin/env bash
# Scan generated premium-mobile assets for credentials and reusable capabilities.
set -euo pipefail

ROOTS=(
  "apps/mobile/dist/financial-os-mobile/browser"
  "apps/mobile/android/app/src/main/assets/public"
  "apps/mobile/ios/App/App/public"
)

GOOGLE_QUERY_PREFIX='X-Goog-'
AWS_QUERY_PREFIX='X-Amz-'
PATTERN="link-(sandbox|development|production)-|public-(sandbox|development|production)-|access-(sandbox|development|production)-|sb_(secret|service_role)_[A-Za-z0-9]|Authorization[[:space:]]*:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{20,}|${GOOGLE_QUERY_PREFIX}Signature=|${AWS_QUERY_PREFIX}Signature="
ERRORS=0

for root in "${ROOTS[@]}"; do
  if [[ ! -d "$root" ]]; then
    continue
  fi

  if grep -RIlE "$PATTERN" "$root" >/dev/null 2>&1; then
    echo "ERROR: Restricted credential or capability pattern found under $root"
    ERRORS=$((ERRORS + 1))
  fi
done

if [[ "$ERRORS" -gt 0 ]]; then
  echo "FAIL: Premium-mobile generated assets contain restricted material."
  exit 1
fi

echo "PASS: Premium-mobile generated assets contain no restricted credential patterns."
