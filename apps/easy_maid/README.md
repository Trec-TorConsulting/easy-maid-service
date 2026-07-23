## Easy Maid

Custom Frappe app for **Easy Maid Service** — layered on top of ERPNext.

Adds only what ERPNext lacks natively for field service:

- **Booking** — one-time or recurring cleaning agreement.
- **Service Visit** — a single scheduled cleaning occurrence.
- **Crew Assignment** — cleaner(s) assigned to a visit.
- Dispatch board + crew calendar + the unified Frappe UI (Vue) frontend.

Everything else (leads/quoting, invoicing, payments, bookkeeping, HR/payroll) uses **native
ERPNext**. See `../../openspec/changes/bootstrap-easy-maid-erpnext/` for the full spec.

### Install (onto the isolated instance)

```bash
bench get-app easy_maid /path/to/apps/easy_maid
bench --site easymaid.trector.com install-app easy_maid
```

#### License

MIT
