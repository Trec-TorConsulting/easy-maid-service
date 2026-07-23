# Easy Maid Service

Back-office + customer portal for a New Jersey cleaning company, built on a **new, isolated**
Frappe + ERPNext instance. One place for **owners**, **clients**, and **cleaners**: leads,
quotes, bookings (one-time + recurring), crew dispatch, invoicing, Stripe payments, payroll,
and bookkeeping.

> ⚠️ **Isolation rule:** This is a brand-new instance. **Never touch** the existing Frappe
> server (namespace `frappe`, site `client.trector.com`).

## Where things live

| Path | What |
| --- | --- |
| `openspec/` | Specs & changes. **Source of truth for what to build.** |
| `openspec/changes/bootstrap-easy-maid-erpnext/` | The foundational change (proposal, design, 8 specs, tasks) |
| `apps/easy_maid/` | Custom Frappe app (DocTypes, hooks, fixtures, Vue frontend) |
| `deploy/k8s/easymaid/` | Raw Kubernetes manifests for the isolated instance |
| `brand/` | Starter brand assets (logo, favicon, icons) + generator |
| `docs/FULL-DEPLOY.md` | The required release workflow |
| `AGENTS.md` | Build conventions & guardrails for AI agents |

## Key facts (decided)

- **Platform:** K3s homelab; `frappe/erpnext:version-16`, MariaDB 10.11, Redis 7.2, Longhorn, Traefik.
- **Namespace / host:** `easymaid` / `easymaid.trector.com` (TLS via `letsencrypt`).
- **App install:** stock image + `bench get-app easy_maid` (no custom image required).
- **Payments:** Stripe hosted checkout. **Locale/tax:** New Jersey, USD, configurable tax template.
- **Policy:** 24-hour minimum cancel/reschedule notice (server-enforced).
- **Frontend:** single Frappe UI (Vue) app with Owner / Client / Cleaner experiences.

## Getting started (for the build agent)

1. Read `AGENTS.md`, then `openspec/changes/bootstrap-easy-maid-erpnext/`.
2. Implement `tasks.md` top-to-bottom (each task has an **Acceptance** check).
3. Ship via the **Full Deploy** workflow in `docs/FULL-DEPLOY.md`.

Validate specs anytime:

```bash
openspec validate --all --strict
```
