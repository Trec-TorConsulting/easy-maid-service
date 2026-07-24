# Full Deploy Workflow

The **canonical release process** for the Easy Maid Service repo. Whenever a change is
described as a **"Full Deploy"**, execute every step below in order. Do not skip steps.

> Guardrails: pushing, opening/merging PRs, and merging to `main` are non-reversible/shared
> actions. Confirm with the owner before the **merge to `main`** step unless explicitly
> pre-authorized for that change.

## Steps

### 1. Branch
- Create a topic branch off the latest `main`.
- Naming: `type/short-description` (e.g., `feat/booking-doctype`, `fix/ingress-tls`,
  `chore/brand-assets`). Use OpenSpec change names where they map cleanly
  (e.g., `feat/bootstrap-easy-maid-erpnext`).

```bash
git checkout main && git pull --ff-only
git checkout -b feat/<short-description>
```

### 2. Commit
- Stage related changes only; keep commits focused.
- Use **Conventional Commits** one-line subjects: `type(scope): subject`
  (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`).
- Reference the OpenSpec change in the body when applicable.

```bash
git add -A
git commit -m "feat(bookings): add Booking and Service Visit DocTypes"
```

### 3. Push
```bash
git push -u origin feat/<short-description>
```

### 4. Open a complete, well-documented PR
Open a PR into `main` with a thorough description. Required sections:
- **Summary** — what & why (link the OpenSpec change / spec files).
- **Changes** — bulleted list of what changed.
- **Testing** — how it was validated (commands, `openspec validate`, manual steps).
- **Deployment impact** — namespaces/manifests touched; confirm the existing `frappe`
  instance is unaffected.
- **Screenshots / artifacts** — where relevant (UI, generated assets).
- **Checklist** — secrets not committed, docs updated, specs/tasks updated.

Use the repository PR template at `.github/pull_request_template.md`.

```bash
gh pr create --base main --head feat/<short-description> \
  --title "feat(scope): subject" \
  --body-file .github/pr-body.md   # or inline --body
```

### 5. Wait / monitor GitHub Actions (PR checks)
- Watch the PR's checks until they complete.

```bash
gh pr checks --watch
# or inspect a run:
gh run list --branch feat/<short-description>
gh run watch <run-id>
```
- If a check **fails**: read the logs (`gh run view <run-id> --log-failed`), fix, commit,
  push, and re-monitor. Do **not** proceed to merge with failing checks.

### 6. Merge to `main`, then monitor post-merge Actions
- Only when **all PR checks are green** (and review/approval per policy is satisfied).
- Prefer **squash merge** with a clean conventional title. Delete the branch after merge.

```bash
gh pr merge --squash --delete-branch
```
- After merge, monitor any `main`-triggered workflows (build/deploy/release):

```bash
gh run list --branch main
gh run watch <run-id>
```
- If a post-merge workflow fails, triage immediately (fix-forward via a new branch/PR, or
  roll back the offending commit). For infra, remember: the `easymaid` namespace is isolated
  and can be rolled back without affecting the existing `frappe` instance.

## Definition of Done for a Full Deploy
- [ ] Branch created from up-to-date `main`
- [ ] Focused, conventional commits
- [ ] Branch pushed
- [ ] Complete, well-documented PR opened
- [ ] All PR GitHub Actions checks green
- [ ] Merged to `main` (squash, branch deleted)
- [ ] Post-merge GitHub Actions monitored and green

## Optional helper

Run a non-destructive preflight before creating a branch/PR:

```bash
bash scripts/full_deploy_prepare.sh feat/<short-description>
```
