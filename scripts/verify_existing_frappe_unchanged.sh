#!/usr/bin/env bash
set -euo pipefail

# Runtime script to verify existing frappe site remains healthy while easymaid evolves.
# Requires network access to both hosts.

EASYMAID_URL="${EASYMAID_URL:-https://easymaid.trector.com}"
EXISTING_FRAPPE_URL="${EXISTING_FRAPPE_URL:-https://www.trector.com}"

check_url() {
  local label="$1"
  local url="$2"
  echo "-- Checking $label: $url"
  local code
  code="$(curl -sS -o /tmp/${label}.html -w "%{http_code}" "$url")"
  echo "$label HTTP: $code"
  if [[ "$code" != "200" && "$code" != "301" && "$code" != "302" ]]; then
    echo "FAIL: $label returned unexpected HTTP code"
    return 1
  fi
  return 0
}

pass=0
fail=0

if check_url "easymaid" "$EASYMAID_URL"; then
  pass=$((pass + 1))
else
  fail=$((fail + 1))
fi

if check_url "existing_frappe" "$EXISTING_FRAPPE_URL"; then
  pass=$((pass + 1))
else
  fail=$((fail + 1))
fi

echo "-- Summary"
echo "PASS checks: $pass"
echo "FAIL checks: $fail"

if [[ "$fail" -ne 0 ]]; then
  echo "Existing frappe verification failed; investigate before merge."
  exit 1
fi

echo "Existing frappe verification passed."
