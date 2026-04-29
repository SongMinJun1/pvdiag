<!-- markdownlint-disable MD013 -->

# BR-20260430-252 Single File Line Diet

## Summary
- This branch reduces generated `pvdiag_single.py` line count and re-audits payload necessity.
- The single-file payload still uses `source_text`; zip/base64 are still not used.
- Runtime diagnosis semantics are unchanged.

## What Changed
- Before: `EMBEDDED_TEXT_FILES` expanded each embedded source file as thousands of line literals.
- After: embedded source text is stored as UTF-8 JSON chunks:
  - `EMBEDDED_TEXT_JSON_CHUNKS`
  - `EMBEDDED_TEXT_FILES = json.loads("".join(...))`
- The underlying payload digest, file count, and runtime extraction semantics remain equivalent.
- A second omit-audit removed only files that passed conalog execution and 8/8 key artifact comparison when absent.

## Removed After Payload Necessity Re-Audit
- `research/__init__.py`
- `research/prognostics/__init__.py`
- `artifacts/fault6_fixed_result_provenance_v1.json`
- `artifacts/runtime_chain_dependency_audit_v1.json`
- `artifacts/runtime_chain_dependency_audit_v1.md`

## Kept After Payload Necessity Re-Audit
- `fault6_label_and_algorithm_preview_v1.csv` is kept because omit-audit produced a 7/8 comparison result.
- raw-only runtime scripts and `heuristic_display_registry_v1.py` are kept because runtime imports and raw-only chain execution depend on them.

## Result
- payload files: 11
- payload text bytes: 422550
- single file line count: 339
- single file bytes: 477767
- previous line count: 10031
- previous bytes: 562302
- line reduction: 9692 lines
- byte reduction: 84535 bytes
- key artifact comparison: 8/8 pass

## Reproduction Commands
```bash
python3 tools/build_pvdiag_single_py.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br252_delivery --snapshot-output /private/tmp/pvdiag_br252_snapshot.json --clean-output-dir
python3 /private/tmp/pvdiag_br252_delivery/pvdiag_single.py --single-self-test
python3 /private/tmp/pvdiag_br252_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br252_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_br251_conalog --single-output-root /private/tmp/pvdiag_br252_conalog --json-output /private/tmp/pvdiag_br252_compare.json
```

## Boundary
- This is not an algorithm diet.
- This does not remove raw-only runtime modules.
- This removes generated-file line noise and payload entries that are not needed for current one-file runtime/result reproduction.
