<!-- markdownlint-disable MD013 -->

# BR-20260430-244 Single File Delivery Export

## Summary
- This patch adds a final export step for the generated `pvdiag_single.py` artifact.
- The professor-facing delivery folder is forced to contain exactly one file: `pvdiag_single.py`.
- Runtime algorithm semantics are unchanged.

## Why This Patch Exists
- BR-242 created the generated single-file runner.
- BR-243 added quickstart and handoff readiness checks.
- This branch closes the remaining handoff ambiguity: internal docs, manifests, checkers, and package folders are useful for us, but they are not part of the professor-facing deliverable.

## Added Guardrails
- `tools/export_pvdiag_single_delivery.py`
  - runs `tools/check_pvdiag_single_handoff.py` before export by default.
  - refuses non-empty output directories unless `--clean-output-dir` is explicitly passed.
  - copies only `pvdiag_single.py`.
  - verifies the output directory contains exactly `pvdiag_single.py`.
  - verifies source/export SHA-256 equality.
  - optionally writes an internal manifest outside the professor delivery folder.
- `research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py`
  - exports to a temporary folder.
  - asserts the professor-facing folder contains exactly one file.
  - asserts the exported file matches the generated source file.
  - runs `--single-self-test` from the exported location.

## Reproduction Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py tools/export_pvdiag_single_delivery.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py tools/check_pvdiag_single_handoff.py
python3 tools/export_pvdiag_single_delivery.py --output-dir /private/tmp/pvdiag_single_professor_delivery_br244
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 /private/tmp/pvdiag_single_professor_delivery_br244/pvdiag_single.py --single-self-test
```

## Operator-Facing Change
- None to diagnosis results.
- The only operational change is delivery packaging clarity: send the exported `pvdiag_single.py` file, not the whole runtime pack.

## Next Step
- Use the BR-244 export command when preparing the professor handoff.
- If field-trial CSVs arrive later, run the exported `pvdiag_single.py` against the real `--data-root` and compare outputs through the existing single/modular comparison helper when needed.
