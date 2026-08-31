#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -gt 0 ]]; then
  ROOTS=("$@")
else
  ROOTS=("deploy/k8s/easymaid")
fi

fail=0
SEARCH="rg"
if ! command -v rg >/dev/null 2>&1; then
  SEARCH="grep"
fi

search() {
  local pattern="$1"
  local path="$2"
  if [[ "$SEARCH" == "rg" ]]; then
    rg -n "$pattern" "$path"
  else
    grep -R -n -E "$pattern" "$path"
  fi
}

echo "== K8s guardrail checks =="

for ROOT in "${ROOTS[@]}"; do
  if [[ ! -d "$ROOT" ]]; then
    echo "Missing $ROOT"
    fail=1
    continue
  fi

  echo "-- Checking $ROOT"

  # 1) Isolation: no frappe namespace references
  if search "namespace:[[:space:]]*frappe" "$ROOT" >/tmp/easymaid_k8s_guardrails.tmp 2>/dev/null; then
    echo "FAIL: found forbidden frappe namespace references"
    cat /tmp/easymaid_k8s_guardrails.tmp
    fail=1
  else
    echo "PASS: no frappe namespace references"
  fi

  # 2) Node exclusion patterns present
  if search "node05|node06" "$ROOT" >/tmp/easymaid_k8s_guardrails.tmp 2>/dev/null; then
    echo "PASS: node05/node06 exclusion markers present"
  else
    echo "FAIL: node05/node06 exclusion markers missing"
    fail=1
  fi

  # 3) PDB resources present
  if search "kind:[[:space:]]*PodDisruptionBudget" "$ROOT" >/tmp/easymaid_k8s_guardrails.tmp 2>/dev/null; then
    echo "PASS: PodDisruptionBudget resources present"
  else
    echo "FAIL: PodDisruptionBudget resources missing"
    fail=1
  fi

  # 4) Required ingress exists
  if [[ -f "$ROOT/ingress.yaml" ]]; then
    echo "PASS: ingress manifest present"
  else
    echo "FAIL: ingress manifest missing"
    fail=1
  fi
done

rm -f /tmp/easymaid_k8s_guardrails.tmp

if [[ "$fail" -ne 0 ]]; then
  echo "K8s guardrail checks failed."
  exit 1
fi

echo "K8s guardrail checks passed."
