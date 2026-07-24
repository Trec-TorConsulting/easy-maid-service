#!/usr/bin/env bash
set -euo pipefail

# Scan tracked git history for obvious credential patterns.
# Uses git log -p on tracked content only; complement with current-tree scan.

regexes=(
  'sk_(live|test)_[A-Za-z0-9]{16,}'
  'pk_(live|test)_[A-Za-z0-9]{16,}'
  'whsec_[A-Za-z0-9]{16,}'
  'AKIA[0-9A-Z]{16}'
  '-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'
)

failed=0
for regex in "${regexes[@]}"; do
  if git --no-pager log -p --all -- . | rg -n --pcre2 "$regex" >/tmp/easymaid_history_scan.tmp 2>/dev/null; then
    echo "Potential historical secret match for pattern: $regex"
    head -n 40 /tmp/easymaid_history_scan.tmp
    failed=1
  fi
done

rm -f /tmp/easymaid_history_scan.tmp

if [[ "$failed" -ne 0 ]]; then
  echo "Git history secret scan failed. Consider rotating credentials and rewriting history if needed."
  exit 1
fi

echo "Git history secret scan passed."
