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

- [x] 3.1 Write MariaDB 10.11.18 `StatefulSet` + `Service` with a Longhorn RWO volumeClaimTemplate
- [x] 3.2 Write three Redis 8 deployments + services (cache, queue, socketio)
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

- [x] 10.1 Create Company "Maidurday Cleaning Service" (abbr `EMS`) with currency, fiscal year, and chart of accounts
- [x] 10.2 Create service Items (Standard/Deep/Move-In-Out/Recurring/Add-ons) as non-stock with Price List rates
- [x] 10.3 Configure a **configurable NJ** Sales Taxes and Charges Template (rate editable without a code deploy)
- [x] 10.4 Create Customer Groups (Residential/Commercial) and employee department/designation
- [x] 10.5 Define roles & permissions and user-permission scoping for Owner/Client/Cleaner
- [x] 10.6 Apply "Maidurday Cleaning Service" branding (name, logo, print formats)
- [x] 10.7 Package the above as `easy_maid` fixtures for reproducible setup
- **Acceptance:** a fresh site + `bench install-app easy_maid` + fixtures yields the Company, service Items, NJ tax template, groups, and roles without manual steps.

## 11. Leads & quoting (native CRM)

- [x] 11.1 Build the public "Request a Quote" Web Form → Lead (source = Website) with anti-spam
- [x] 11.2 Verify Lead → Opportunity → Quotation flow with service Items and tax totals
- [x] 11.3 Configure branded Quotation PDF/email and Quotation → Sales Order conversion
- **Acceptance:** submitting the public form creates a Lead; a Quotation with tax totals can be produced and converted to a Sales Order.

## 12. Invoicing, payments & bookkeeping (native)

- [x] 12.1 Enable Sales Invoice generation from completed one-time visits
- [x] 12.2 Wire recurring invoices via Subscription/recurring Sales Order for recurring Bookings
- [x] 12.3 Configure the **Stripe** Payment Gateway with hosted checkout; record Payment Entry on success (keys/webhook secret in Secrets)
- [x] 12.4 Handle payment failure/retry UX and reconciliation to Paid
- [ ] 12.5 Verify GL postings and financial reports (AR, P&L, GL); enable branded receipt PDF
- **Acceptance:** a completed visit invoices correctly; a Stripe test payment reconciles the invoice to Paid and posts correct GL entries; AR/P&L reflect it.

## 13. Employee management & payroll (native HR)

- [x] 13.1 Configure Employee records with cleaning attributes (skills/certifications, service area)
- [x] 13.2 Configure shifts/availability used during dispatch
- [ ] 13.3 Configure salary structures and run a test payroll (Salary Slips + accounting entries)
- [ ] 13.4 Verify cleaners cannot view others' payroll data
- **Acceptance:** a test payroll run produces Salary Slips + accounting entries; a cleaner cannot see another employee's pay.

## 14. Unified frontend (Frappe UI / Vue)

- [x] 14.1 Scaffold the Vue SPA in `easy_maid` using Frappe UI with session auth
- [x] 14.2 Implement route guards and role-based landing (Owner/Client/Cleaner)
- [x] 14.3 Owner dashboard: metrics (upcoming visits, unassigned jobs, revenue/AR) + navigation
- [x] 14.4 Client experience: book one-time/recurring, view/reschedule/cancel visits, view/pay invoices
- [x] 14.5 Cleaner experience: today's assigned jobs, start/complete actions (mobile-friendly)
- [x] 14.6 Apply consistent "Maidurday Cleaning Service" branding and responsive layout
- **Acceptance:** each role logs in to its own landing; a client can book + pay; a cleaner can complete a job on mobile; branding is consistent.

## 15. Public website (Maidurday marketing site)

- [x] 15.1 Create a shared public base template (Maidurday header/nav/footer, brand palette, responsive) used by all public pages
- [x] 15.2 Build the Home/landing page (hero, value props, primary CTAs: Request a Quote, Book Online, Client Login)
- [x] 15.3 Build Services, Pricing (from Price List), About, Contact (phone/email/hours + form), Service Areas (NJ towns), and FAQ pages
- [x] 15.4 Add Privacy Policy and Terms of Service pages linked in the footer
- [x] 15.5 Add a curated Testimonials section (staff-managed; no public rating submission) and seed sample entries
- [x] 15.6 Enable the native Blog (Blog Category + Blog Post) and seed 5 starter articles as UNPUBLISHED drafts
- [x] 15.7 Add per-page SEO metadata (title/description/Open Graph); ensure `/sitemap.xml` and `/robots.txt` serve
- [x] 15.8 Wire CTAs to the quote form, self-service booking, and client login routes
- **Acceptance:** `/` returns a branded Maidurday home page without login; all listed pages render responsively; the 5 blog drafts exist and are NOT publicly visible until published; `/sitemap.xml` and `/robots.txt` return 200; no page shows legacy "Easy Maid Service" text.

## 16. Notifications & reminders

- [ ] 16.1 Configure Email Account(s)/SMTP and (optional) SMS Settings with credentials sourced only from Secrets/site config
- [x] 16.2 Create branded Email Templates/Notifications for: booking confirmation, cleaner assignment, ~24h visit reminder, invoice issued, payment receipt, and quote acknowledgement
- [x] 16.3 Implement/enable an idempotent scheduled reminder (at most one send per visit event) via the worker/scheduler
- [x] 16.4 Respect client channel consent/opt-out; include an unsubscribe mechanism in marketing email
- [x] 16.5 Ensure sends are enqueued to background workers and failures are logged (never block the originating user action)
- **Acceptance:** a test booking triggers a branded confirmation; a visit ~24h out triggers exactly one reminder; a recorded payment triggers a receipt; disabling a notification stops only that message; no provider secret is committed.

## 17. Self-service signup & online booking

- [x] 17.1 Build a public signup flow that provisions a portal User (client role only) + linked Customer, with email verification
- [x] 17.2 Build an online booking flow (service, address, one-time date or recurring cadence) that creates a Booking + Service Visit(s) with no staff step
- [x] 17.3 Show an itemized estimate (subtotal + NJ tax + total) before confirmation; recompute the authoritative price SERVER-SIDE from Price List + tax template
- [x] 17.4 Offer optional prepay via Stripe hosted checkout that reconciles the invoice; otherwise allow pay-later from the portal
- [x] 17.5 Throttle + anti-spam the public signup/booking endpoints and validate all input server-side
- [x] 17.6 Scope new users to their own records only; fall back to Request-a-Quote (Lead) for out-of-area/custom jobs
- **Acceptance:** a brand-new visitor can sign up, verify email, book, and (optionally) pay online with no staff step; the server rejects a tampered client total; a new client cannot see any other customer's data; an out-of-area request becomes a Lead.

## 18. Maidurday branding & Desk declutter

- [x] 18.1 Sweep code/display strings so no user-facing surface shows legacy "Easy Maid Service" (e.g., SPA header in `apps/easy_maid/frontend/src/App.vue`, page titles) — display brand is "Maidurday Cleaning Service"
- [x] 18.2 Confirm the ERPNext Company is "Maidurday Cleaning Service" (abbr `EMS`) and Website/Navbar/Letter Head branding is Maidurday
- [x] 18.3 Hide all stock Frappe/ERPNext workspaces on the Desk, keeping only the Maidurday cleaning workspace(s); do not remove DocType permissions
- [x] 18.4 Re-apply the declutter after migrations (`after_migrate`) so stock workspaces do not reappear
- **Acceptance:** `/app` shows only Maidurday workspace(s) for owners/employees; stock ERPNext workspaces stay hidden after `bench migrate`; no legacy "Easy Maid Service" display text remains; internal ids (`easy_maid`, `EMS`, roles) unchanged.

## 19. Security, backups & verification

- [x] 19.1 Confirm all secrets are in Kubernetes Secrets/site config (nothing sensitive in git)
- [ ] 19.2 Verify least-privilege permissions: clients/cleaners see only their own records
- [x] 19.3 Add scheduled DB + files backup CronJob with retention
- [ ] 19.4 Confirm PDBs and node affinity; run a disruption/restore drill
- [ ] 19.5 End-to-end smoke test of all capabilities against `easymaid.trector.com` (including public website, notifications, and self-service signup/booking)
- [ ] 19.6 Confirm the existing `frappe` instance/site is unaffected
- **Acceptance:** no secrets in git history; permission scoping verified; a backup restore drill succeeds; the existing `frappe` site still serves.

## 20. Release (Full Deploy workflow)

- [ ] 20.1 Initialize the git repo and create the GitHub remote
- [x] 20.2 Add CI GitHub Actions (lint/build/`openspec validate`) so PRs have checks to monitor
- [ ] 20.3 For each change, follow `docs/FULL-DEPLOY.md`: branch → commit → push → complete PR → monitor Actions
- [ ] 20.4 On green checks, merge to `main` (squash, delete branch) and monitor post-merge Actions
- **Acceptance:** CI runs `openspec validate --all --strict` on PRs; the Full Deploy steps in `docs/FULL-DEPLOY.md` are followed for each change.
