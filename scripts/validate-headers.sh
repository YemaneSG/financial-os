#!/usr/bin/env bash
# Assert that the deployed Firebase Hosting URL serves the frozen security headers.
# Usage: validate-headers.sh <hosting-url>
# Exits non-zero if any required header is missing or incorrect.
# Controls: S-02, APP-03, NET-01.
set -euo pipefail

URL="${1:?Usage: validate-headers.sh <hosting-url>}"
URL="${URL%/}" # Strip trailing slash.
TARGET="${URL}/index.html"

echo "Fetching headers from: ${TARGET}"
HEADERS=$(curl -sIL --max-time 15 "${TARGET}" | sed -n '/^HTTP\//,$p')

ERRORS=0

assert_header() {
  local header_name="$1"
  local expected_pattern="$2"
  local actual
  actual=$(echo "$HEADERS" | grep -i "^${header_name}:" | tail -1 | sed 's/^[^:]*: *//')
  if echo "$actual" | grep -qE "$expected_pattern"; then
    echo "PASS: ${header_name}"
  else
    echo "FAIL: ${header_name}"
    echo "      expected to match: ${expected_pattern}"
    echo "      got: ${actual}"
    ERRORS=$((ERRORS + 1))
  fi
}

assert_hsts_min_age() {
  local actual
  local max_age
  actual=$(echo "$HEADERS" | grep -i "^strict-transport-security:" | tail -1 | sed 's/^[^:]*: *//')
  max_age=$(echo "$actual" | sed -nE 's/.*max-age=([0-9]+).*/\1/ip')
  if [[ -n "$max_age" ]] && (( 10#$max_age >= 31536000 )); then
    echo "PASS: strict-transport-security max-age"
  else
    echo "FAIL: strict-transport-security max-age"
    echo "      expected at least 31536000 seconds"
    echo "      got: ${actual}"
    ERRORS=$((ERRORS + 1))
  fi
}

assert_absent() {
  local header_name="$1"
  local forbidden_pattern="$2"
  local actual
  actual=$(echo "$HEADERS" | grep -i "^content-security-policy:" | head -1)
  if echo "$actual" | grep -qE "$forbidden_pattern"; then
    echo "FAIL: ${header_name} contains forbidden pattern: ${forbidden_pattern}"
    ERRORS=$((ERRORS + 1))
  else
    echo "PASS: ${header_name} does not contain ${forbidden_pattern}"
  fi
}

# ── Frozen CSP (S-02, implementation-contracts.md §6) ─────────────────────
assert_header "content-security-policy" "default-src 'self'"
assert_header "content-security-policy" "frame-ancestors 'none'"
assert_header "content-security-policy" "object-src 'none'"
assert_header "content-security-policy" "base-uri 'self'"
assert_absent  "content-security-policy" "unsafe-inline"
assert_absent  "content-security-policy" "unsafe-eval"

# ── Additional required headers (APP-03, NET-01) ─────────────────────────
assert_hsts_min_age
assert_header "strict-transport-security" "includeSubDomains"
assert_header "strict-transport-security" "preload"
assert_header "x-content-type-options"    "nosniff"
assert_header "referrer-policy"           "no-referrer"
assert_header "permissions-policy"        "camera=\(self\)"

if [[ "$ERRORS" -gt 0 ]]; then
  echo ""
  echo "FAIL: ${ERRORS} header assertion(s) failed. Deploy blocked."
  exit 1
fi

echo ""
echo "PASS: All required security headers are present and correct."
