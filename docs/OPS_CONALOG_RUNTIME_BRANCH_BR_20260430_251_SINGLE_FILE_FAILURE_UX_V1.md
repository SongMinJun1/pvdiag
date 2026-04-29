<!-- markdownlint-disable MD013 -->

# BR-20260430-251 Single File Failure UX

## Summary
- This branch hardens the professor-facing `pvdiag_single.py` failure messages before handoff.
- Runtime diagnosis semantics are unchanged.
- The single-file self-test now verifies embedded payload integrity without requiring external Python packages.

## UX Changes
- `--single-self-test` runs before dependency checks, so a recipient can confirm file integrity even before installing `pandas`, `numpy`, `torch`, `openpyxl`, and `tqdm`.
- Missing package failures return exit code `2` and show the exact install command:
  - `pip install pandas numpy torch openpyxl tqdm`
- Missing or invalid input data root failures return exit code `3` and show:
  - `--data-root /path/to/data`
  - sibling `data/` fallback location
  - output/log directory
- `--single-keep-runtime` still prints the kept runtime path on dependency or data-root failures.

## Reproduction Commands
```bash
python3 tools/build_pvdiag_single_py.py
python3 research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br251_delivery --snapshot-output /private/tmp/pvdiag_br251_snapshot.json --clean-output-dir
python3 /private/tmp/pvdiag_br251_delivery/pvdiag_single.py --single-self-test
python3 /private/tmp/pvdiag_br251_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br251_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_br250_desktop_conalog --single-output-root /private/tmp/pvdiag_br251_conalog --json-output /private/tmp/pvdiag_br251_compare.json
```

## Result
- failure UX smoke: pass
- handoff check: pass
- delivery export closeout: pass
- conalog single-file run: pass
- key artifact comparison: 8/8 pass
- algorithm semantics changed: no

## Delivery Boundary
- This is a handoff usability patch only.
- Field-trial truth-label evaluation is still blocked until real KTC ESS CSV and final labels arrive.
