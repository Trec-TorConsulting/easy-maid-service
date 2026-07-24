# Easy Maid ERPNext setup automation

This package provides idempotent backend setup for tasks 10.x.

## Bootstrap command

Run on the target site after `easy_maid` is installed:

```bash
bench --site easymaid.trector.com execute easy_maid.easy_maid.setup.bootstrap.bootstrap_easymaid_defaults
```

## What it creates/updates

- Company: `Easy Maid Service` (USD, New Jersey, USA)
- Fiscal year: current calendar year (`FY-<year>`) set as company default
- Customer Groups: `Residential`, `Commercial`
- Employee structures: Department `Cleaning`, Designations `Cleaner`, `Lead Cleaner`
- Employee profile fields on `Employee`: `Service Area`, `Cleaning Skills`, `Certifications`
- Shift types: `Easy Maid Morning`, `Easy Maid Afternoon`
- Payroll scaffold (best effort): salary components + `Easy Maid Cleaner Monthly` salary structure
- Service catalog items (`EMS-*`) + Standard Selling prices
- NJ tax template: `NJ Sales Tax` (configurable later)
- Roles: `Easy Maid Owner`, `Easy Maid Client`, `Easy Maid Cleaner`
- Basic website app-name branding
- Stripe settings bootstrap (when site config keys are present)
- Native `Request a Quote` Web Form seed (best effort)
- Branded Quotation print format seed `Easy Maid Quotation` (best effort)
- Branded Sales Invoice print format seed `Easy Maid Receipt` (best effort)
- Letterhead seed `Easy Maid Letterhead`

## Fixture workflow

After running bootstrap on a configured site:

```bash
bench --site easymaid.trector.com export-fixtures
```

Fixtures are configured in `easy_maid/hooks.py` so records can be versioned.

## Live verification helper

From repo root:

```bash
bash scripts/verify_all_live.sh easymaid.trector.com
```

This runs bootstrap + capability smoke + unresolved-task evidence matrix.

## Stripe config keys (site config)

Bootstrap can configure Stripe settings automatically if these keys exist in site config:

- `stripe_publishable_key`
- `stripe_secret_key`
- `stripe_webhook_secret` (optional)

Example:

```bash
bench --site easymaid.trector.com set-config stripe_publishable_key "pk_test_..."
bench --site easymaid.trector.com set-config stripe_secret_key "sk_test_..."
bench --site easymaid.trector.com set-config stripe_webhook_secret "whsec_..."
```

## Payroll note

Bootstrap seeds payroll configuration where supported, but actual payroll verification still requires a live site run (salary slips + accounting entries).
