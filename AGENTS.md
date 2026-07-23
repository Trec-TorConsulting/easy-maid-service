# AGENTS.md — build guide & guardrails

Read this first. It exists so **any model (including a smaller/cheaper one)** can implement
this project safely and correctly. Follow it literally.

## The golden rules

1. **Source of truth = OpenSpec.** Build exactly what
   `openspec/changes/bootstrap-easy-maid-erpnext/` (proposal, design, specs, tasks) says.
   If code and spec disagree, the spec wins — or update the spec first.
2. **Isolation.** Never read, modify, or reference the existing `frappe` namespace / site
   `client.trector.com`. This project is 100% isolated in namespace `easymaid`.
3. **Prefer native ERPNext.** Only add custom DocTypes/code where the design says ERPNext
   lacks a native feature (Booking, Service Visit, Crew Assignment, dispatch UI).
4. **Never commit secrets.** Stripe keys, DB passwords, admin passwords, kubeconfig → live in
   Kubernetes Secrets / site config only. Commit `*.example.yaml` templates, never real values.
5. **Tell the truth.** If something is unknown or can't be verified (e.g., exact NJ tax rate,
   cluster access), say so and stop — do not invent values.

## Work loop (do this for every task)

1. Pick the next unchecked task in `tasks.md` (top-to-bottom order matters).
2. Read the linked spec/design section for that capability.
3. Implement the smallest change that satisfies the task.
4. Verify against the task's **Acceptance** line.
5. Run `openspec validate --all --strict` (must stay green).
6. Check the box in `tasks.md`.
7. Ship via **Full Deploy** (`docs/FULL-DEPLOY.md`) — but only create/push a GitHub repo and
   merge to `main` when explicitly authorized.

## Fixed decisions (do not re-litigate)

| Topic | Decision |
| --- | --- |
| Image | `frappe/erpnext:version-16` |
| Namespace / host | `easymaid` / `easymaid.trector.com` |
| DB / cache | MariaDB 10.11 / Redis 7.2 (cache, queue, socketio) |
| Storage | Longhorn — sites **RWX**, DB **RWO** |
| Ingress / TLS | Traefik, cert resolver `letsencrypt` |
| Node affinity | Exclude `node05` and `node06` on all workloads |
| App install | `bench get-app easy_maid` onto stock image |
| Payments | Stripe hosted checkout |
| Locale / currency | New Jersey, USA / USD; configurable NJ tax template |
| Cancel policy | 24h minimum notice, enforced server-side (admin override) |
| Frontend | Single Frappe UI (Vue) app, role-based (Owner/Client/Cleaner) |

## Exact commands / conventions

- Validate specs: `openspec validate --all --strict`
- Lint manifests: `yamllint -d relaxed deploy`
- Commits: **Conventional Commits** one-line subjects (`feat(scope): subject`).
- Branches: `type/short-description` (map to OpenSpec change names when possible).
- K8s manifests: model after `~/Projects/HomeLab-Redo/frappe/` (raw manifests, **not Helm**).
- Frappe module for custom DocTypes: **"Easy Maid"** → `apps/easy_maid/easy_maid/easy_maid/doctype/`.
- Recurring visits: implement as an **idempotent** scheduled job (unique per Booking + date).

## Custom data model (from design D5) — build these

- **Booking**: Customer + Address, service Item(s), price, one-time date OR recurrence rule
  (frequency/interval/start/end-or-count), optional link to Sales Order / Subscription.
- **Service Visit**: link Booking, scheduled window, status
  (Scheduled/In Progress/Completed/Cancelled), completion timestamp, notes.
- **Crew Assignment**: Employee + role on a Service Visit, with overlap validation.

## When to STOP and ask a human

- You need a secret/credential (Stripe, DB, admin, kubeconfig).
- You need to create/push a GitHub repo or merge to `main`.
- A verifiable fact is missing (tax rate, DNS, account ownership).
- A task would touch anything outside this repo or the `easymaid` namespace.
