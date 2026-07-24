#!/usr/bin/env bash
set -euo pipefail

# Non-destructive helper to prepare and validate a Full Deploy PR branch.
# Does not push or merge.

branch="${1:-}"
if [[ -z "$branch" ]]; then
  echo "Usage: bash scripts/full_deploy_prepare.sh <type/short-description>"
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repository."
  exit 1
fi

current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "Current branch: $current_branch"

echo "== Running local gates =="
openspec validate --all --strict
PYTHONPATH=apps/easy_maid .venv-assets/bin/python -m unittest discover -s apps/easy_maid/easy_maid/tests -p 'test_*.py' -v
bash scripts/check_no_secrets.sh
bash scripts/check_git_history_secrets.sh
bash scripts/verify_k8s_guardrails.sh

echo "== Suggested next commands =="
echo "git checkout main && git pull --ff-only"
echo "git checkout -b $branch"
echo "git add -A && git commit -m 'feat(scope): subject'"
echo "git push -u origin $branch"
echo "gh pr create --base main --head $branch"
echo "gh pr checks --watch"
