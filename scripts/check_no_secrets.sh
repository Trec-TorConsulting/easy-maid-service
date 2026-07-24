#!/usr/bin/env bash
set -euo pipefail

# Lightweight repo secret scan (pattern-based).
# This complements policy: real credentials belong in Kubernetes Secrets/site config.

regexes=(
  'sk_(live|test)_[A-Za-z0-9]{16,}'
  'pk_(live|test)_[A-Za-z0-9]{16,}'
  'whsec_[A-Za-z0-9]{16,}'
  'AKIA[0-9A-Z]{16}'
  '-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'
)

globs=(
  '--glob=!**/*.example.yaml'
  '--glob=!**/secret.example.yaml'
  '--glob=!**/.venv-assets/**'
  '--glob=!**/node_modules/**'
)

failed=0
for regex in "${regexes[@]}"; do
  if rg -n --pcre2 "$regex" . "${globs[@]}" >/tmp/easymaid_secret_scan.tmp 2>/dev/null; then
    echo "Potential secret match for pattern: $regex"
    cat /tmp/easymaid_secret_scan.tmp
    failed=1
  fi
done

rm -f /tmp/easymaid_secret_scan.tmp

if [[ "$failed" -ne 0 ]]; then
  echo "Secret scan failed. Move secrets to Kubernetes Secret or site config."
  exit 1
fi

echo "Secret scan passed."
