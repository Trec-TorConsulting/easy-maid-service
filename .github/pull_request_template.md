## Summary
- What changed and why.
- Link OpenSpec change and relevant specs/tasks.

## Changes
- 
- 

## Testing
- [ ] `openspec validate --all --strict`
- [ ] `PYTHONPATH=apps/easy_maid .venv-assets/bin/python -m unittest discover -s apps/easy_maid/easy_maid/tests -p 'test_*.py' -v`
- [ ] `bash scripts/check_no_secrets.sh`
- [ ] `bash scripts/check_git_history_secrets.sh`
- [ ] `bash scripts/verify_k8s_guardrails.sh`

## Deployment Impact
- Namespace(s) touched:
- Manifests touched:
- Existing `frappe` instance unaffected: [ ] Verified

## Screenshots / Artifacts
- 

## Checklist
- [ ] No secrets committed
- [ ] Docs updated (`docs/FULL-DEPLOY.md`, smoke/runbook updates)
- [ ] OpenSpec tasks/specs updated appropriately
- [ ] CI green
