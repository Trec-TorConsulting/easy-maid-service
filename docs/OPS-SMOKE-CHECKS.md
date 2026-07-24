# Easy Maid Smoke Checks

This runbook verifies runtime tasks that cannot be proven by static checks alone.

## 10.x bootstrap + fixtures

Run bootstrap on site:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.bootstrap.bootstrap_easymaid_defaults
```

Export fixtures after bootstrap:

```bash
bench --site easymaid.trector.com export-fixtures
```

Verify baseline data:

```bash
bench --site easymaid.trector.com console
# in console
frappe.db.exists('Company', 'Easy Maid Service')
frappe.db.exists('Sales Taxes and Charges Template', 'NJ Sales Tax')
frappe.get_all('Item', filters={'item_code': ['like', 'EMS-%']}, pluck='name')
```

## 11.x lead to quote to booking smoke

Public quote page:

- Visit `/request-quote`
- Submit a real payload and confirm a `Lead` with `source=Website`
- Verify native Web Form exists in Desk: `Web Form` named `Request a Quote`

Native CRM flow smoke in one command:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.run_lead_to_booking_smoke
```

Expected output includes keys:

- `lead`
- `opportunity`
- `quotation`
- `sales_order`
- `booking`

Verify branded print format exists and renders:

```bash
bench --site easymaid.trector.com console
# in console
frappe.db.exists('Print Format', 'Easy Maid Quotation')
frappe.db.exists('Print Format', 'Easy Maid Receipt')
frappe.db.exists('Letter Head', 'Easy Maid Letterhead')
```

## 12.x invoicing smoke

Generate invoice from a completed one-time visit:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.generate_invoice_for_visit --kwargs '{"visit_name":"SV-YYYY-00001"}'
```

Enable recurring billing artifacts on recurring booking:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.ensure_recurring_billing_for_booking --kwargs '{"booking_name":"BK-YYYY-00001"}'
```

Create hosted payment request URL for unpaid invoice:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.create_invoice_payment_request --kwargs '{"invoice_name":"SINV-YYYY-00001"}'
```

Create or reuse a mock unpaid invoice if needed:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.create_or_get_mock_unpaid_invoice
```

Simulate webhook-success reconciliation to Payment Entry:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.reconcile_invoice_payment --kwargs '{"invoice_name":"SINV-YYYY-00001"}'
```

Stripe runtime readiness helper:

```bash
bash scripts/verify_stripe_runtime.sh easymaid.trector.com
```

If bench is not on PATH:

```bash
BENCH_CMD='/home/frappe/frappe-bench/env/bin/bench' bash scripts/verify_stripe_runtime.sh easymaid.trector.com
```

Stripe key storage location:

- Commit-safe template: deploy/k8s/easymaid/secret.example.yaml
- Real values (do not commit): deploy/k8s/easymaid/secret.yaml
- Dev template: deploy/k8s/easymaid-dev/secret.example.yaml
- Dev real values (do not commit): deploy/k8s/easymaid-dev/secret.yaml

Populate these fields in Kubernetes Secret stringData:

- stripe-publishable-key
- stripe-secret-key
- stripe-webhook-secret

Validate retry behavior by re-running the same command after a failed/abandoned payment attempt; invoice should remain unpaid and return a payment URL again.

## 14.x portal smoke

Authenticated API checks:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.owner_dashboard_metrics
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.client_portal_snapshot
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.cleaner_today_jobs
```

## 13.x employee + dispatch availability smoke

Validate custom employee fields and shifts exist:

```bash
bench --site easymaid.trector.com console
# in console
frappe.db.exists('Custom Field', {'dt': 'Employee', 'fieldname': 'easymaid_service_area'})
frappe.db.exists('Shift Type', 'Easy Maid Morning')
frappe.db.exists('Shift Type', 'Easy Maid Afternoon')
```

Availability query for dispatch planning:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.api.available_cleaners --kwargs '{"scheduled_start":"2026-07-24 09:00:00","scheduled_end":"2026-07-24 11:00:00"}'
```

Payroll isolation check (as a cleaner user): cleaner should only see own Employee/Salary Slip records.

Payroll scaffold check:

```bash
bench --site easymaid.trector.com console
# in console
frappe.db.exists('Salary Structure', 'Easy Maid Cleaner Monthly')
```

Run payroll smoke for one cleaner employee:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.run_payroll_smoke --kwargs '{"employee":"HR-EMP-00001"}'
```

Run permission scope smoke (least-privilege):

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.run_permission_scope_smoke
```

Run consolidated capability smoke summary:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.run_capability_smoke_summary
```

Run unresolved-task evidence matrix directly:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.smoke.run_task_evidence_matrix
```

One-command live verification helper:

```bash
bash scripts/verify_all_live.sh easymaid.trector.com
```

If bench is not on PATH:

```bash
BENCH_CMD='/home/frappe/frappe-bench/env/bin/bench' bash scripts/verify_all_live.sh easymaid.trector.com
```

Summary now includes:

- Lead -> Opportunity -> Quotation -> Sales Order -> Booking flow with quote total/tax checks
- Invoice generation + payment-request URL generation (when a completed visit exists)

## 6.3 and 5.3 live checks

```bash
bench --site easymaid.trector.com list-apps
```

Should include:

- `frappe`
- `erpnext`
- `easy_maid`

## Dev k3s caveat (easymaid-dev)

If `easy_maid` is installed on `dev.easymaid.trector.com` but runtime pods do not
have persistent app code, Python pods can fail with `ModuleNotFoundError: easy_maid`.

Use this recovery helper from repo root:

```bash
bash scripts/recover_dev_easymaid_uninstall.sh easymaid-dev dev.easymaid.trector.com
```

This removes `easy_maid` from the dev site and resets `sites/apps.txt` back to
stock (`frappe`, `erpnext`) so pods can recover.

TLS/websocket:

```bash
curl -I https://easymaid.trector.com
```

Expect HTTP 200/301 with valid certificate chain from Let's Encrypt.

## 15.1 secret hygiene checks

Run repository secret scan:

```bash
bash scripts/check_no_secrets.sh
bash scripts/check_git_history_secrets.sh
```

Ensure real gateway keys only exist in Kubernetes Secrets and site config.

## Final verification handoff

For remaining runtime-only tasks (11.2, 11.3, 12.3, 12.5, 13.3, 13.4, 15.2, 15.5, 15.6):

1. Run bootstrap and fixture export on site.
2. Run capability summary and payroll smoke helpers.
3. Validate Stripe hosted checkout and webhook-to-Payment Entry reconciliation.
4. Validate cleaner least-privilege in a real cleaner session.
5. Confirm existing `frappe` namespace/site remains unaffected.

Existing-site health verification:

```bash
EASYMAID_URL=https://easymaid.trector.com \
EXISTING_FRAPPE_URL=https://www.trector.com \
bash scripts/verify_existing_frappe_unchanged.sh
```

Release preflight helper:

```bash
bash scripts/full_deploy_prepare.sh feat/<short-description>
```

Static k8s guardrail verification:

```bash
bash scripts/verify_k8s_guardrails.sh
```

Optional scope to a specific tree:

```bash
bash scripts/verify_k8s_guardrails.sh deploy/k8s/easymaid-dev
```

Disruption drill plan (print-only helper):

```bash
bash scripts/disruption_drill_plan.sh
```

Full deploy workflow monitor helper:

```bash
bash scripts/full_deploy_monitor.sh feat/<short-description>
```
