#!/usr/bin/env bash
set -euo pipefail

# Helper for 16.3/16.4 to monitor PR and post-merge workflows.
# Requires gh CLI auth and repository remote.

BRANCH="${1:-}"
if [[ -z "$BRANCH" ]]; then
  echo "Usage: bash scripts/full_deploy_monitor.sh <branch>"
  exit 1
fi

echo "== Monitoring PR checks for branch: $BRANCH =="
gh pr checks --watch || true

echo "== Recent workflow runs on branch =="
gh run list --branch "$BRANCH" --limit 10 || true

echo "== After merge, monitor main =="
echo "gh run list --branch main --limit 10"
echo "gh run watch <run-id>"
