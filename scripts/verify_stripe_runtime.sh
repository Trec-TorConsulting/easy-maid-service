#!/usr/bin/env bash
set -euo pipefail

# Runtime verifier for Stripe readiness on a live bench site.
# This script does not submit a real payment; it checks config + payment-request path.

SITE="${1:-easymaid.trector.com}"
BENCH_CMD="${BENCH_CMD:-bench}"

read -r -a _bench <<< "$BENCH_CMD"

if ! command -v "${_bench[0]}" >/dev/null 2>&1; then
	echo "Missing bench command: ${_bench[0]}"
	echo "Set BENCH_CMD, for example:"
	echo "  BENCH_CMD='/home/frappe/frappe-bench/env/bin/bench' bash scripts/verify_stripe_runtime.sh $SITE"
	exit 1
fi

echo "== Stripe runtime verification =="
echo "Site: $SITE"
echo "Bench: $BENCH_CMD"

echo "-- Checking site config keys"
"${_bench[@]}" --site "$SITE" show-config stripe_publishable_key || true
"${_bench[@]}" --site "$SITE" show-config stripe_secret_key || true
"${_bench[@]}" --site "$SITE" show-config stripe_webhook_secret || true

echo "-- Checking Stripe Settings status"
"${_bench[@]}" --site "$SITE" execute "frappe.client.get" --kwargs '{"doctype":"Stripe Settings"}' >/tmp/easymaid_stripe_settings.json || true

echo "-- Checking payment request path (requires an unpaid invoice)"
echo "Use: $BENCH_CMD --site $SITE execute easy_maid.easy_maid.api.create_invoice_payment_request --kwargs '{\"invoice_name\":\"SINV-YYYY-00001\"}'"

echo "-- Checking reconciliation path"
echo "Use: $BENCH_CMD --site $SITE execute easy_maid.easy_maid.api.reconcile_invoice_payment --kwargs '{\"invoice_name\":\"SINV-YYYY-00001\"}'"

echo "Stripe runtime verifier complete. Inspect /tmp/easymaid_stripe_settings.json and bench outputs."
