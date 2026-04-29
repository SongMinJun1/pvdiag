<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260430_243_SINGLE_FILE_HANDOFF_POLISH_V1

## Summary
- This patch adds the final handoff polish around the generated `pvdiag_single.py` delivery artifact.
- It adds a professor-facing quickstart and a machine-checkable handoff readiness script.
- Runtime semantics are unchanged.

## Why
- BR-242 created and validated the generated single-file runner.
- The next risk is not algorithm correctness, but handoff ambiguity: what to install, how to run, what output to open, and how to check the file before sending.

## Added Files
- `release/conalog_full_runtime_v1/PVDIAG_SINGLE_QUICKSTART.md`
- `tools/check_pvdiag_single_handoff.py`

## Handoff Check
The checker verifies:

- `pvdiag_single.py` exists.
- `pvdiag_single_manifest_v1.json` exists.
- required embedded runtime modules are listed in the manifest.
- Windows embedded runtime/cache files are not embedded.
- generated single file compiles.
- generated single file self-test succeeds.

## Boundary
- No truth rows, thresholds, engine semantics, or operator-facing diagnosis rules are changed.
- This is a delivery-readiness patch only.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py tools/check_pvdiag_single_handoff.py
python3 tools/check_pvdiag_single_handoff.py
python3 release/conalog_full_runtime_v1/pvdiag_single.py --single-self-test
python3 release/conalog_full_runtime_v1/pvdiag_single.py \
  --data-root /Users/b9gc/pvdiag/data \
  --output-root /private/tmp/pvdiag_single_handoff_polish_conalog \
  --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data \
  --sites conalog
git diff --check
```
