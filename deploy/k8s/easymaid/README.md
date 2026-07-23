# deploy/k8s/easymaid — Kubernetes manifests

Raw manifests for the **new, isolated** Easy Maid Service ERPNext instance.
Namespace: `easymaid`. Host: `easymaid.trector.com`. **Do not touch the existing `frappe` namespace.**

Model these after the proven pattern in `~/Projects/HomeLab-Redo/frappe/` (raw manifests, NOT Helm),
retargeted to this namespace/host. See `openspec/changes/bootstrap-easy-maid-erpnext/design.md`
(Migration Plan) for deploy order, and `tasks.md` sections 2–6.

## Cluster facts to reuse (from HomeLab-Redo)
- StorageClass: `longhorn` (default). Sites PVC = **RWX**, MariaDB = **RWO**.
- Ingress: Traefik, cert resolver `letsencrypt` (Let's Encrypt + Cloudflare DNS).
- Node affinity: **exclude `node05` and `node06`** on every workload.
- Images: `frappe/erpnext:version-16`, `mariadb:10.11`, `redis:7.2`.
- Local registry (optional): `registry.registry:5000`.

## Files to create (checklist)
- [x] `namespace.yaml`
- [ ] `configmap.yaml` — site name, host, CORS, cookie/session config
- [ ] `secret.example.yaml` — template only; real Secret applied out-of-band
- [ ] `networkpolicy.yaml` — scope traffic to `easymaid`
- [ ] `mariadb.yaml` — StatefulSet + Service (Longhorn RWO)
- [ ] `redis-cache.yaml` / `redis-queue.yaml` / `redis-socketio.yaml`
- [ ] `pvc-sites.yaml` — Longhorn RWX
- [ ] `frappe-python.yaml` / `frappe-socketio.yaml` / `frappe-worker.yaml` / `frappe-scheduler.yaml`
- [ ] `ingress.yaml` — Traefik for `easymaid.trector.com`
- [ ] `site-init-job.yaml` — `bench new-site … --install-app erpnext --install-app easy_maid`
- [ ] `backup-cronjob.yaml`, `pdb.yaml`

## Acceptance
- `kubectl apply -k deploy/k8s/easymaid` succeeds (dry-run: `kubectl apply -k . --dry-run=server`).
- `yamllint -d relaxed deploy` passes.
- No manifest references the `frappe` namespace.
- All workloads carry the node05/node06 exclusion affinity.
