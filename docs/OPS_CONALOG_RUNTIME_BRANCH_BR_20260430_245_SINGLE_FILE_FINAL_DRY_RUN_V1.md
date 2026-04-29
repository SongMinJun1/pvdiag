<!-- markdownlint-disable MD013 -->

# BR-20260430-245 Single File Final Dry Run

## Summary
- This branch step locks the final dry-run expectation for the professor-facing `pvdiag_single.py` handoff.
- The dry run starts from a fresh export folder and validates that the exported file can self-test outside the repo tree.
- Runtime diagnosis semantics are unchanged.

## Reproduction Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py tools/export_pvdiag_single_delivery.py tools/check_pvdiag_single_delivery_closeout.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_single_delivery_closeout_br247 --clean-output-dir
```

## Success Criteria
- export folder contains exactly `pvdiag_single.py`.
- source/export SHA-256 values match.
- exported `pvdiag_single.py --single-self-test` passes.
- closeout summary reports `algorithm_semantics_changed=0`.

## Result
- Covered by the BR-247 closeout checker and snapshot.
