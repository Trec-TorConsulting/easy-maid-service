## Context

Maidurday Cleaning Service (built on the custom `easy_maid` app) needs one system for owners,
clients, and cleaners to run a cleaning business. We are standing up a **new, isolated**
Frappe + ERPNext instance on an existing
K3s homelab cluster and adding a thin custom app (`easy_maid`) only for the field‑service
capabilities ERPNext lacks natively.

Current state / constraints (verified against the `HomeLab-Redo` cluster repo):

- Cluster: K3s, 7 nodes (4× RPi5 ARM64, 1× Jetson GPU `node05`, 2× x86 incl. `node06` video/TPU).
- Existing Frappe runs in namespace `frappe`, image `frappe/erpnext:version-16`,
  MariaDB 10.11, Redis 7.2, site `client.trector.com`. **This must not be touched.**
- Storage: Longhorn default StorageClass (3 replicas); RWX supported for shared sites.
- Ingress: Traefik with cert resolver `letsencrypt` (Let's Encrypt + Cloudflare DNS),
  base domain `trector.com`.
- Local registry at `registry.registry:5000` (in‑cluster) / NodePort `30500`.
- Node affinity convention: exclude `node05` and `node06` from general workloads.
- App‑per‑folder manifest convention (namespace, configmap, secret, deployment, service,
  ingress, pvc, pdb). Existing Frappe uses **raw manifests, not Helm**.

Stakeholders: business owners (admin/finance), clients (booking/paying), cleaners (doing jobs).

## Goals / Non-Goals

**Goals:**
- A fully isolated ERPNext instance at `easymaid.trector.com` with its own DB, cache, storage, and site.
- Maximum reuse of native ERPNext (CRM, Selling, Accounts, HR, Subscriptions, Appointment).
- A minimal `easy_maid` app adding only Booking, Service Visit, and crew dispatch.
- One Frappe UI (Vue) frontend with three role‑based experiences.
- Reproducible, GitOps‑friendly Kubernetes manifests stored in this repo.

**Non-Goals:**
- Post‑clean rating collection, native mobile apps, route/GPS optimization, multi‑company.
  (A public marketing website IS in scope; the site shows staff‑curated testimonials only,
  not customer‑submitted ratings.)
- Reusing or migrating anything from the existing `frappe` instance.

## Decisions

### D1: Raw K8s manifests (match existing convention), not Helm
Mirror the proven `frappe/` manifest pattern into a new `deploy/k8s/easymaid/` folder in this
repo, retargeted to namespace `easymaid` and host `easymaid.trector.com`.
- **Why:** Consistency with the existing, working deployment; full control; no Helm chart drift.
- **Alternatives:** Frappe Helm chart (more moving parts, diverges from cluster convention);
  Frappe Cloud (rejected — user runs their own cluster).

### D2: Isolation strategy
Dedicated namespace `easymaid` with its own MariaDB StatefulSet, three Redis deployments,
sites RWX PVC, Secrets, and site `easymaid.trector.com`. No cross‑namespace references.
- **Why:** Hard isolation from `frappe`; independent lifecycle and backups.
- **Risk mitigation:** NetworkPolicy scoped to the namespace; separate Secrets.

### D3: Align to `version-16`
Use `frappe/erpnext:version-16` to match the cluster's proven image (user confirmed,
overriding the earlier version‑15 preference).
- **Why:** Known‑good on this hardware/arch; one image line to maintain.

### D4: Native‑first module mapping
| Business need | ERPNext native | Custom `easy_maid` |
| --- | --- | --- |
| Lead capture | Web Form → Lead | quote request form tweaks |
| Qualify/quote | Opportunity, Quotation | service‑item picker |
| Convert to job | Sales Order | Booking generator |
| Recurring billing | Subscription / recurring Sales Order | — |
| One‑time/recurring schedule | (Appointment for estimates) | **Booking**, **Service Visit** |
| Dispatch/crew | (none) | **Crew Assignment**, dispatch board, calendar |
| Invoice/pay | Sales Invoice, Payment Entry, Payment Gateway | — |
| Bookkeeping | Accounts / GL | — |
| HR/payroll | Employee, Shift, Payroll | cleaner skill/area fields |

- **Why:** Least custom code; leverage ERPNext's tested accounting and HR.

### D5: Custom data model (`easy_maid`)
- **Booking**: link Customer + Address, service Item(s), price, one‑time date or recurrence
  rule (frequency/interval/start/end‑or‑count), optional link to Sales Order/Subscription.
- **Service Visit**: link Booking, scheduled window, status
  (Scheduled/In Progress/Completed/Cancelled), completion timestamp, notes.
- **Crew Assignment** (child table or linked DocType on Service Visit): Employee + role,
  with overlap validation.
- A scheduled job (Frappe scheduler) materializes future Service Visits from active recurring
  Bookings up to a configurable horizon, idempotently (unique per Booking+date).

### D6: Frontend — Frappe UI (Vue) single SPA
One Vue SPA bundled in `easy_maid`, using Frappe's session auth and REST/RPC. Route guards
select the Owner/Client/Cleaner experience from the user's roles. Server‑side permissions
(DocType role permissions + query conditions) are the source of truth; the UI only hides
what the user can't access.
- **Why:** Native auth/session, one deploy, no separate CORS/SPA host to secure.
- **Alternatives:** Separate Next.js app (more infra, more attack surface); pure ERPNext
  portal (weaker UX for the unified experience).

### D7: Payments — Stripe
Configure the ERPNext **Stripe** Payment Gateway for client online payments; a successful
charge creates a Payment Entry reconciling the Sales Invoice. Use Stripe hosted checkout so
no card data touches our servers (PCI SAQ‑A). Stripe API keys/webhook secret live in
Kubernetes Secrets / site config, never in the repo.

### D8: Locale, currency & tax — New Jersey, USA
Company locale is **New Jersey, USA**; base currency **USD**. Configure a NJ Sales Taxes and
Charges Template. Note (verify at build time, not legal advice): NJ generally taxes many
cleaning/janitorial services — model the current NJ state sales tax rate as a configurable
tax template so the rate can be updated without code changes.

### D9: Cancellation / reschedule policy — 24‑hour minimum notice
Clients MUST give at least **24 hours notice** to cancel or reschedule a Service Visit. Inside
the 24‑hour window, self‑service cancel/reschedule is blocked in the portal (owner/admin may
override). This is enforced server‑side on the Service Visit, not only in the UI.

### D10: App install — stock image + `bench get-app` (no custom image required)
Install `easy_maid` onto the stock `frappe/erpnext:version-16` image at site‑init time via
`bench get-app` from the repo, rather than baking a custom image. Keeps the registry step
optional; revisit a custom image only if build time/reproducibility demands it.

### D11: Release process — "Full Deploy"
All shipping follows the documented Full Deploy workflow (see `docs/FULL-DEPLOY.md`):
Branch → Commit → Push → complete well‑documented PR → wait/monitor GitHub Actions →
on green checks, merge to `main` → monitor post‑merge Actions.

### D12: Brand assets
"Maidurday Cleaning Service" brand assets — **green** palette (primary `#5BB07A`→`#1E4F3A`,
mint accent `#C6F6D5`), a single `M` monogram + sparkle — live in `brand/` (SVG + PNG +
`favicon`), generated reproducibly via `brand/generate_assets.py`. The **display** brand is
"Maidurday"; internal identifiers (app `easy_maid`, module "Easy Maid", roles "Easy Maid *",
abbreviation `EMS`, asset path `/assets/easy_maid/`) intentionally stay unchanged.

### D13: Security & secrets
All credentials (DB root/app, admin password, gateway keys) live in Kubernetes Secrets and
site config, not in manifests or git. TLS enforced end‑to‑end; HTTP→HTTPS redirect.
Least‑privilege DocType permissions with user‑permission scoping so clients/cleaners only see
their own records.

### D14: Public website on the same Frappe instance
Serve the public marketing site from the **same** `easymaid` instance/host using Frappe's
website layer (portal `www/` Jinja pages and/or Web Page + Blog Post DocTypes), not a separate
app or host. A shared base template provides the Maidurday header/nav/footer; pages: Home,
Services, Pricing, About, Contact, Service Areas, FAQ, Privacy, Terms. Blog uses native Blog
Post/Blog Category; seed 5 posts as **unpublished drafts**. Testimonials are staff‑curated
content (fixture/DocType), not a public submission form. Add per‑page SEO meta/Open Graph and
rely on Frappe's generated `sitemap.xml` + a `robots.txt`.
- **Why:** One deploy, one auth/session domain, native SEO/blog; no extra host to secure.
- **Alternatives:** Separate static/marketing site (more infra, brand/data drift) — rejected.

### D15: Notifications & reminders — native ERPNext tooling
Use native **Notification**, **Email Template**, **Print Format**, and **SMS Settings** with
Email Account(s) for delivery; enqueue sends via background workers. Cleaning‑specific triggers
(booking confirmation, ~24h visit reminder, receipt on payment, quote acknowledgement) are
configured as Notifications/scheduled events so admins can edit copy/timing without a code
deploy. Reminder generation must be **idempotent** (at most one send per event). Provider
credentials live in Secrets/site config. SMS is optional and gated on a configured provider +
client consent; marketing email includes unsubscribe.
- **Why:** Configurable, branded, no bespoke delivery stack; reuses the worker/queue already deployed.

### D16: Self‑service signup & online booking
Allow a brand‑new prospect to self‑register (portal User + linked Customer, client role only)
with email verification, then book a one‑time or recurring cleaning end‑to‑end and optionally
prepay via Stripe hosted checkout — no staff step. Price/tax are always recomputed **server‑side**
from the Price List + NJ tax template (never trust client totals). Public signup/booking
endpoints are throttled and anti‑spam protected; out‑of‑area/custom jobs fall back to the
Request‑a‑Quote (Lead) flow. New users are permission‑scoped to their own records.
- **Why:** Removes the manual bottleneck for standard jobs while preserving quoting for edge cases.

### D17: Maidurday display branding + Desk declutter
The **display** brand across Desk, portal, website, and documents is "Maidurday Cleaning
Service"; internal identifiers stay `easy_maid`/"Easy Maid"/`EMS` (see D12). The ERPNext Desk
(`/app`, `/desk`) is decluttered to Maidurday‑only: stock Frappe/ERPNext workspaces are hidden
(reversibly, without removing DocType permissions) and re‑applied after every `bench migrate`
(migrate re‑syncs stock workspaces). Legacy "Easy Maid Service" display strings in code (e.g.,
the SPA header) are swept to "Maidurday Cleaning Service".
- **Why:** Owners/employees get a focused cleaning back office; brand is consistent everywhere.

## Risks / Trade-offs

- **[Custom dispatch is non‑native] →** Keep Booking/Visit/Assignment minimal and lean on
  native Calendar/permissions; document clearly what is custom vs native.
- **[RWX Longhorn contention on shared sites PVC] →** Use the proven Longhorn RWX pattern from
  the existing instance; set replica count and monitor; keep workers modest.
- **[ARM64/x86 mixed scheduling] →** Use multi‑arch `frappe/erpnext` images; exclude
  `node05`/`node06` via nodeAffinity as the cluster convention requires.
- **[Recurring visit generation duplicates/gaps] →** Idempotent generator keyed on
  Booking+date; horizon + backfill guard; unit tests for the recurrence rule.
- **[Payment gateway PCI/secret handling] →** Use hosted gateway checkout (no card data on our
  servers); keep keys in Secrets; never log secrets.
- **[Accidental impact to existing `frappe`] →** Separate namespace, Secrets, PVCs, and host;
  NetworkPolicy; review manifests before apply.

## Migration Plan

This is greenfield (no data migration). Deploy order:
1. Create `easymaid` namespace, Secrets, ConfigMap, NetworkPolicy.
2. Deploy MariaDB (StatefulSet + Longhorn RWO) and the three Redis instances.
3. Deploy Frappe web/socketio/worker/scheduler; mount shared sites RWX PVC.
4. Run site‑init Job: `bench new-site easymaid.trector.com … --install-app erpnext --install-app easy_maid`.
5. Apply Traefik ingress + TLS for `easymaid.trector.com`; verify HTTPS and `/socket.io`.
6. Run ERPNext config (company, CoA, items, tax, groups, roles) via bench/fixtures.
7. Build/push `easy_maid` image to `registry.registry:5000` (if a custom image is used) and roll out.
8. Configure payment gateway and scheduled backups; verify PDBs.

**Rollback:** delete the `easymaid` namespace and its PVCs; the existing `frappe` instance is
unaffected. Restore from the most recent backup if re‑deploying.

## Resolved Decisions (previously open)

- **Payment gateway:** Stripe (hosted checkout). → D7
- **Locale / currency / tax:** New Jersey, USA / USD / configurable NJ sales‑tax template. → D8
- **Cancellation window:** 24‑hour minimum notice, enforced server‑side. → D9
- **App image:** stock `frappe/erpnext:version-16` + `bench get-app easy_maid` (custom image optional). → D10
- **Release process:** Full Deploy workflow. → D11 / `docs/FULL-DEPLOY.md`
- **Brand assets:** starter assets generated in `brand/`. → D12

## Open Questions

- Final production brand artwork (starter assets are placeholders).
- Confirm the current NJ state sales‑tax rate and any local surcharges at build time.
- Stripe account ownership + webhook endpoint hardening details.
