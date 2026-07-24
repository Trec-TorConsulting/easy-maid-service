#!/usr/bin/env bash
set -euo pipefail

# One-command runtime verifier for unresolved OpenSpec tasks.
# Requires bench + live site context.

SITE="${1:-easymaid.trector.com}"
BENCH_CMD="${BENCH_CMD:-bench}"

read -r -a _bench <<< "$BENCH_CMD"

if ! command -v "${_bench[0]}" >/dev/null 2>&1; then
  echo "Missing bench command: ${_bench[0]}"
  echo "Set BENCH_CMD, for example:"
  echo "  BENCH_CMD='/home/frappe/frappe-bench/env/bin/bench' bash scripts/verify_all_live.sh $SITE"
  exit 1
fi

echo "== Easy Maid live verification =="
echo "Site: $SITE"
echo "Bench: $BENCH_CMD"

echo "-- Running bootstrap defaults"
"${_bench[@]}" --site "$SITE" execute easy_maid.easy_maid.setup.bootstrap.bootstrap_easymaid_defaults >/tmp/easymaid_bootstrap.json || true

echo "-- Running consolidated capability smoke"
"${_bench[@]}" --site "$SITE" execute easy_maid.easy_maid.setup.smoke.run_capability_smoke_summary >/tmp/easymaid_capability.json || true

echo "-- Running task evidence matrix"
"${_bench[@]}" --site "$SITE" execute easy_maid.easy_maid.setup.smoke.run_task_evidence_matrix >/tmp/easymaid_matrix.json || true

echo "== Raw outputs =="
echo "bootstrap: /tmp/easymaid_bootstrap.json"
echo "capability: /tmp/easymaid_capability.json"
echo "matrix: /tmp/easymaid_matrix.json"

if command -v jq >/dev/null 2>&1; then
  echo "== Matrix (status per task) =="
  jq -r 'to_entries[] | "\(.key): \(.value.status) - \(.value.evidence)"' /tmp/easymaid_matrix.json || true
else
  echo "jq not found; open /tmp/easymaid_matrix.json to review status per task."
fi

echo "== Suggested follow-up =="
echo "1) Review PARTIAL/MANUAL entries in matrix output"
echo "2) Run Stripe hosted checkout test payment"
echo "3) Validate existing frappe namespace/site unaffected"
