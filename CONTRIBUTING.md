# Contributing to Easy Maid Service

Thanks for your interest. This repository is public for transparency, but it is a
**proprietary** project (see [`LICENSE`](LICENSE)). External contributions are accepted only
by invitation and at the maintainer's discretion. Please open an issue to discuss before
investing significant time.

> Read [`AGENTS.md`](AGENTS.md) first — it defines the non-negotiable guardrails for this
> codebase (isolation, spec-driven delivery, no secrets in git).

## Golden rules

1. **OpenSpec is the source of truth.** Build exactly what the active change in
   `openspec/changes/` specifies. If code and spec disagree, update the spec first.
2. **Isolation.** Never read, modify, or reference the pre-existing `frappe` namespace or the
   site `client.trector.com`. This project lives entirely in the `easymaid` namespace.
3. **Prefer native ERPNext.** Only add custom DocTypes or code where the design says ERPNext
   lacks a native feature.
4. **Never commit secrets.** Stripe keys, DB/admin passwords, and kubeconfig live in
   Kubernetes Secrets / site config. Commit `*.example` templates only.
5. **Tell the truth.** If a value can't be verified (tax rate, DNS, cluster access), say so
   and stop — don't invent it.

## Development workflow

1. Pick the next unchecked task in the active change's `tasks.md` (top-to-bottom order).
2. Read the linked spec/design section, then implement the smallest change that satisfies it.
3. Verify against the task's **Acceptance** line.
4. Keep specs green: `openspec validate --all --strict`.
5. Lint manifests: `yamllint -d relaxed deploy`.
6. Check the box in `tasks.md`.

For a local environment, see [`deploy/local/README.md`](deploy/local/README.md).

## Branches & commits

- **Branches:** `type/short-description` (map to the OpenSpec change name when possible),
  e.g. `feat/booking-recurrence`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) one-line subjects,
  e.g. `feat(booking): add recurrence rule validation`.
  Common types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`.

## Pull requests

- `main` is protected: land changes via pull request. Direct pushes, force-pushes, and branch
  deletion are blocked; a linear history is required.
- Keep PRs focused and small. Fill out the PR template, link the relevant task/spec, and note
  how you verified the change.
- Resolve all conversations before merge. Use **squash merge** (the only enabled strategy);
  the source branch is deleted automatically.
- CI is not enabled at this time; verify locally before requesting review.

## Reporting bugs & requesting features

Use the issue templates. For anything security-related, do **not** open a public issue —
follow [`SECURITY.md`](SECURITY.md) instead.

## Code of conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
