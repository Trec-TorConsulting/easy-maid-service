## Why

Easy Maid Service needs a single system where **owners**, **clients**, and **cleaners**
run the entire cleaning business: capturing leads, quoting jobs, booking one‑time and
recurring cleanings, dispatching crews, invoicing, taking payments, running payroll, and
keeping the books. Rather than stitch together point tools, we stand up a dedicated
Frappe + ERPNext instance and reuse native ERPNext for everything it already does well,
adding a thin custom app (`easy_maid`) only for the field‑service pieces ERPNext lacks.

This is a brand‑new, **isolated** instance. It must not touch the existing Frappe server
(namespace `frappe`, site `client.trector.com`).

## What Changes

- Stand up a **new, separate** Frappe + ERPNext deployment (`frappe/erpnext:version-16`)
  on the K3s homelab cluster in a new `easymaid` namespace, reachable at
  `easymaid.trector.com`. Raw Kubernetes manifests live in this repo.
- Create and install a custom Frappe app **`easy_maid`** on the new site.
- Configure the ERPNext backend end‑to‑end for a cleaning company (company, chart of
  accounts, service items, tax, customer/employee groups, roles, permissions).
- Enable **native CRM** for web‑to‑lead capture and quoting (Lead → Opportunity → Quotation).
- Add custom **Booking** and **Service Visit** DocTypes for one‑time and recurring
  (weekly/biweekly/monthly) cleanings, backed by native Sales Order/Subscription billing.
- Add custom **crew scheduling & dispatch** (assign cleaners, crew calendar, complete jobs)
  — ERPNext has **no** native field‑service dispatch.
- Enable **native invoicing, online payments, and bookkeeping** (Sales Invoice, Payment
  Entry, Payment Gateway, GL/Accounts).
- Enable **native HR** for cleaner records, shifts, and payroll.
- Build a **single Frappe UI (Vue) frontend** serving three role‑based experiences:
  Owners/Admins, Clients/Customers, Employees/Cleaners.

### Native ERPNext vs. custom (`easy_maid`)

| Capability | Native ERPNext | Custom in `easy_maid` |
| --- | --- | --- |
| Leads & quoting | Lead, Opportunity, Quotation, Web Form | Web‑to‑lead tuning, service‑item picker |
| Bookings & recurring | Sales Order, Subscription, Appointment | **Booking**, **Service Visit** DocTypes, recurrence generator |
| Scheduling & dispatch | (none) | **Crew Assignment**, dispatch board, crew calendar |
| Invoicing & payments | Sales Invoice, Payment Entry, Payment Gateway, GL | none |
| Employee mgmt & payroll | Employee, Shift, Salary/Payroll | cleaner skills/service‑area fields |
| Frontend | Portal/Desk | **Frappe UI (Vue)** unified app |

## Capabilities

### New Capabilities
- `platform-deployment`: New isolated Frappe/ERPNext instance on K3s — namespace, MariaDB/Redis, workers, Traefik ingress + TLS, Longhorn storage, site bootstrap, and `easy_maid` app install.
- `erpnext-cleaning-config`: ERPNext backend configuration for a cleaning company — company, chart of accounts, service items/price lists, tax, customer/employee groups, roles & permissions.
- `leads-and-quoting`: Native CRM web‑to‑lead capture and quoting through Lead → Opportunity → Quotation.
- `bookings-and-recurring-visits`: Custom Booking/Service Visit DocTypes for one‑time and recurring cleanings, tied to native Sales Order/Subscription billing.
- `scheduling-and-dispatch`: Custom crew assignment, dispatch board, and crew calendar with job completion — the field‑service layer ERPNext lacks.
- `invoicing-and-payments`: Native Sales Invoice, online payment collection, and double‑entry bookkeeping.
- `employee-management-payroll`: Native ERPNext HR for cleaner records, shifts, and payroll.
- `customer-portal-frontend`: Single Frappe UI (Vue) frontend with role‑based experiences for owners, clients, and cleaners.

### Modified Capabilities
<!-- None. This is a greenfield project; no existing specs. -->

## Non-goals

- **Reviews & feedback** (post‑clean ratings) — deferred past day one.
- Mobile native apps (the Frappe UI web app is responsive; no iOS/Android build).
- Marketing website / public content site (only the web‑to‑lead form is in scope).
- Migrating or integrating any data from the existing `frappe` instance.
- Multi‑company / franchise support beyond the single "Easy Maid Service" company.
- Route optimization / GPS tracking of crews.

## Impact

- **New infrastructure**: `easymaid` K3s namespace, MariaDB 10.11, 3× Redis 7.2, Frappe
  web/socketio/worker/scheduler pods, Longhorn PVCs, Traefik ingress + `letsencrypt` TLS
  for `easymaid.trector.com`. New Kubernetes manifests added to this repo.
- **New code**: custom Frappe app `easy_maid` (DocTypes, permissions, hooks, Frappe UI frontend).
- **Dependencies**: Frappe/ERPNext version‑16 images, optional custom app image pushed to
  `registry.registry:5000`; a payment gateway account (e.g., Stripe) for online payments.
- **No impact** to the existing `frappe` namespace/site — fully isolated.
