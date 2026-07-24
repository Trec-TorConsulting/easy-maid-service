#!/usr/bin/env bash
set -euo pipefail

# Print-only drill plan for 15.4. Does not execute disruptive operations.

NAMESPACE="${NAMESPACE:-easymaid}"

echo "== Easy Maid disruption/restore drill plan (print-only) =="
echo "Namespace: $NAMESPACE"

echo "1) Confirm PDBs and workload readiness"
echo "kubectl get pdb -n $NAMESPACE"
echo "kubectl get deploy,statefulset,pods -n $NAMESPACE"

echo "2) Record pre-drill pod placement and app health"
echo "kubectl get pods -n $NAMESPACE -o wide"
echo "curl -I https://easymaid.trector.com"

echo "3) Controlled disruption (choose one worker node hosting easymaid pods)"
echo "kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --force"
echo "# wait for rescheduling and readiness"

echo "4) Restore node"
echo "kubectl uncordon <node>"

echo "5) Post-drill checks"
echo "kubectl get pods -n $NAMESPACE -o wide"
echo "curl -I https://easymaid.trector.com"
echo "bench --site easymaid.trector.com list-apps"

echo "6) Verify existing frappe unaffected"
echo "curl -I https://www.trector.com"
