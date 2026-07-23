## 1. Repo & project scaffolding

- [x] 1.1 Create repo layout: `deploy/k8s/easymaid/` (manifests), `apps/easy_maid/` (custom app source), `brand/` (assets)
- [x] 1.2 Add a top-level `README.md` documenting the instance, hostname, and deploy order
- [x] 1.3 Add `.gitignore` for Frappe/Python/Node artifacts and a place for local secrets (git-ignored)
- [x] 1.4 Confirm starter brand assets in `brand/` (SVG/PNG/`favicon.ico`) and wire them into the app manifest/favicon (placeholders — replace with final artwork later)
- **Acceptance:** `README.md`, `.gitignore`, `AGENTS.md`, `brand/`, `apps/easy_maid/`, and `deploy/k8s/easymaid/` all exist; `openspec validate --all --strict` is green.

## 2. Kubernetes infrastructure (namespace easymaid)

- [x] 2.1 Write `namespace.yaml` for `easymaid`
- [x] 2.2 Write `secret.example.yaml` (DB root/app, admin password, gateway keys) — real values NOT committed
- [x] 2.3 Write `configmap.yaml` (site name `easymaid.trector.com`, host, CORS, cookie/session config)
- [x] 2.4 Write `networkpolicy.yaml` scoping traffic to the `easymaid` namespace
- [x] 2.5 Add `nodeAffinity` snippet excluding `node05` and `node06` to all workloads
- **Acceptance:** `kubectl apply -k deploy/k8s/easymaid --dry-run=server` succeeds; no manifest references the `frappe` namespace; every workload has the node05/node06 exclusion.

## 3. Data & cache services

- [x] 3.1 Write MariaDB 10.11 `StatefulSet` + `Service` with a Longhorn RWO volumeClaimTemplate
- [x] 3.2 Write three Redis 7.2 deployments + services (cache, queue, socketio)
- [x] 3.3 Write `pvc-sites.yaml` — Longhorn RWX PVC for the shared sites directory
- [x] 3.4 Add PDBs for MariaDB and (later) the web deployment
- **Acceptance:** MariaDB and 3 Redis services reach Ready; sites PVC binds as RWX on `longhorn`.

## 4. Frappe/ERPNext workloads

- [x] 4.1 Write `frappe-python` (web/API, port 8000) deployment mounting the sites PVC
- [x] 4.2 Write `frappe-socketio` (port 9000) deployment
- [x] 4.3 Write worker deployment(s) (default/short queues) and the scheduler
- [x] 4.4 Write Services for web and socketio
- [x] 4.5 Add PDB for the web deployment
- **Acceptance:** web pod serves HTTP 200 on `:8000` in-cluster; socketio, a worker, and the scheduler are Running.

## 5. Site bootstrap & app install

- [x] 5.1 App-install strategy (RESOLVED): install `easy_maid` via `bench get-app` from the repo onto the stock `frappe/erpnext:version-16` image at site-init (custom image to `registry.registry:5000` only if needed later)
- [x] 5.2 Write idempotent `site-init-job.yaml`: `bench new-site easymaid.trector.com … --install-app erpnext --install-app easy_maid --set-default`
- [ ] 5.3 Verify the site comes up and both `erpnext` and `easy_maid` are installed
- **Acceptance:** `bench --site easymaid.trector.com list-apps` shows `frappe`, `erpnext`, `easy_maid`; re-running the Job does not error or duplicate the site.

## 6. Ingress & TLS

- [x] 6.1 Write Traefik `ingress.yaml` for `easymaid.trector.com` (`/` → web:8000, `/socket.io` → socketio:9000)
- [x] 6.2 Apply `letsencrypt` cert resolver + HTTP→HTTPS redirect middleware
- [ ] 6.3 Verify valid TLS cert and end-to-end HTTPS + websocket connectivity
- **Acceptance:** `https://easymaid.trector.com` loads with a valid Let's Encrypt cert; HTTP redirects to HTTPS; websocket connects.

## 7. Custom app: easy_maid scaffold

- [x] 7.1 Scaffold the Frappe app `easy_maid` (`bench new-app`) with `hooks.py`, modules, and fixtures dir
- [x] 7.2 Configure app metadata, license, and dependency on `erpnext`
- **Acceptance:** `apps/easy_maid` matches the standard Frappe app layout (`hooks.py`, `modules.txt`, `pyproject.toml`, module package); `required_apps = ["erpnext"]` is set.

## 8. Bookings & recurring visits (custom DocTypes)

- [x] 8.1 Create `Booking` DocType (Customer, Address, service Items, price, one-time date or recurrence rule, links to Sales Order/Subscription)
- [x] 8.2 Create `Service Visit` DocType (Booking link, scheduled window, status, completion timestamp, notes)
- [x] 8.3 Implement recurrence rule fields (frequency/interval/start/end-or-count) with validation
- [x] 8.4 Implement idempotent scheduled generator that materializes future Service Visits up to a configurable horizon
- [x] 8.5 Implement "seed Booking from Sales Order" and cancel-single-visit logic
- [x] 8.6 Enforce the 24-hour minimum cancel/reschedule notice server-side (with Owner/Admin override)
- [x] 8.7 Unit tests for recurrence generation (no duplicates, correct dates, cancel isolation) and the 24-hour policy
- **Acceptance:** unit tests pass; a weekly Booking generates correct non-duplicate visits; a client change <24h before start is rejected server-side.

## 9. Scheduling & dispatch (custom)

- [x] 9.1 Create `Crew Assignment` (Employee + role) on Service Visit with overlap/double-booking validation
- [x] 9.2 Build the dispatch board view (day/range, grouped by status/cleaner, highlight unassigned)
- [x] 9.3 Build the crew calendar filterable by cleaner and status
- [x] 9.4 Implement job start/complete flow (status + completion timestamp; mark eligible for invoicing)
- [x] 9.5 Permission tests: only assigned cleaner can change a visit's status
- **Acceptance:** unassigned visits are visible on the dispatch board; assigning a conflicting cleaner is flagged; a non-assigned cleaner is denied status changes.

## 10. ERPNext cleaning-company configuration (fixtures)

- [ ] 10.1 Create Company "Easy Maid Service" with currency, fiscal year, and chart of accounts
- [ ] 10.2 Create service Items (Standard/Deep/Move-In-Out/Recurring/Add-ons) as non-stock with Price List rates
- [ ] 10.3 Configure a **configurable NJ** Sales Taxes and Charges Template (rate editable without a code deploy)
- [ ] 10.4 Create Customer Groups (Residential/Commercial) and employee department/designation
- [ ] 10.5 Define roles & permissions and user-permission scoping for Owner/Client/Cleaner
- [ ] 10.6 Apply "Easy Maid Service" branding (name, logo placeholder, print formats)
- [ ] 10.7 Package the above as `easy_maid` fixtures for reproducible setup
- **Acceptance:** a fresh site + `bench install-app easy_maid` + fixtures yields the Company, service Items, NJ tax template, groups, and roles without manual steps.

## 11. Leads & quoting (native CRM)

- [ ] 11.1 Build the public "Request a Quote" Web Form → Lead (source = Website) with anti-spam
- [ ] 11.2 Verify Lead → Opportunity → Quotation flow with service Items and tax totals
- [ ] 11.3 Configure branded Quotation PDF/email and Quotation → Sales Order conversion
- **Acceptance:** submitting the public form creates a Lead; a Quotation with tax totals can be produced and converted to a Sales Order.

## 12. Invoicing, payments & bookkeeping (native)

- [ ] 12.1 Enable Sales Invoice generation from completed one-time visits
- [ ] 12.2 Wire recurring invoices via Subscription/recurring Sales Order for recurring Bookings
- [ ] 12.3 Configure the **Stripe** Payment Gateway with hosted checkout; record Payment Entry on success (keys/webhook secret in Secrets)
- [ ] 12.4 Handle payment failure/retry UX and reconciliation to Paid
- [ ] 12.5 Verify GL postings and financial reports (AR, P&L, GL); enable branded receipt PDF
- **Acceptance:** a completed visit invoices correctly; a Stripe test payment reconciles the invoice to Paid and posts correct GL entries; AR/P&L reflect it.

## 13. Employee management & payroll (native HR)

- [ ] 13.1 Configure Employee records with cleaning attributes (skills/certifications, service area)
- [ ] 13.2 Configure shifts/availability used during dispatch
- [ ] 13.3 Configure salary structures and run a test payroll (Salary Slips + accounting entries)
- [ ] 13.4 Verify cleaners cannot view others' payroll data
- **Acceptance:** a test payroll run produces Salary Slips + accounting entries; a cleaner cannot see another employee's pay.

## 14. Unified frontend (Frappe UI / Vue)

- [ ] 14.1 Scaffold the Vue SPA in `easy_maid` using Frappe UI with session auth
- [ ] 14.2 Implement route guards and role-based landing (Owner/Client/Cleaner)
- [ ] 14.3 Owner dashboard: metrics (upcoming visits, unassigned jobs, revenue/AR) + navigation
- [ ] 14.4 Client experience: book one-time/recurring, view/reschedule/cancel visits, view/pay invoices
- [ ] 14.5 Cleaner experience: today's assigned jobs, start/complete actions (mobile-friendly)
- [ ] 14.6 Apply consistent "Easy Maid Service" branding and responsive layout
- **Acceptance:** each role logs in to its own landing; a client can book + pay; a cleaner can complete a job on mobile; branding is consistent.

## 15. Security, backups & verification

- [ ] 15.1 Confirm all secrets are in Kubernetes Secrets/site config (nothing sensitive in git)
- [ ] 15.2 Verify least-privilege permissions: clients/cleaners see only their own records
- [x] 15.3 Add scheduled DB + files backup CronJob with retention
- [ ] 15.4 Confirm PDBs and node affinity; run a disruption/restore drill
- [ ] 15.5 End-to-end smoke test of all capabilities against `easymaid.trector.com`
- [ ] 15.6 Confirm the existing `frappe` instance/site is unaffected
- **Acceptance:** no secrets in git history; permission scoping verified; a backup restore drill succeeds; the existing `frappe` site still serves.

## 16. Release (Full Deploy workflow)

- [ ] 16.1 Initialize the git repo and create the GitHub remote
- [x] 16.2 Add CI GitHub Actions (lint/build/`openspec validate`) so PRs have checks to monitor
- [ ] 16.3 For each change, follow `docs/FULL-DEPLOY.md`: branch → commit → push → complete PR → monitor Actions
- [ ] 16.4 On green checks, merge to `main` (squash, delete branch) and monitor post-merge Actions
- **Acceptance:** CI runs `openspec validate --all --strict` on PRs; the Full Deploy steps in `docs/FULL-DEPLOY.md` are followed for each change.
