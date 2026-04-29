<!-- markdownlint-disable MD013 -->

# BR-20260430-254 Single-File Payload Folding

## Purpose
- BR-253 made the embedded payload discoverable, but `EMBEDDED_TEXT_JSON_CHUNKS` still appeared too early and too visually dense.
- This branch keeps the compact source-text JSON chunk payload while moving it out of the way of the readable executable body.

## Change
- Move generated `EMBEDDED_TEXT_JSON_CHUNKS`, `EMBEDDED_TEXT_FILES`, and `EMBEDDED_FILE_SHA256` below the runner functions.
- Wrap the payload blob with VS Code-compatible folding markers.
  - `# region Embedded source payload (auto-generated; collapse this block in VS Code)`
  - `# endregion`
- Keep `PAYLOAD_FILE_INDEX`, `--single-list-payload`, and `--single-extract-source`.
- Extend smoke/handoff checks so future generated files must keep the foldable payload region.

## Boundary
- No diagnostic algorithm semantics change.
- No payload necessity change: still 11 essential files.
- No base64 or zip payload.
- This is a professor-facing readability/maintainability patch.

## Validation Plan
```bash
python3 tools/build_pvdiag_single_py.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br254_delivery --clean-output-dir
python3 /private/tmp/pvdiag_br254_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br254_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_br251_conalog --single-output-root /private/tmp/pvdiag_br254_conalog --json-output /private/tmp/pvdiag_br254_compare.json
```

## Expected Result
- File top now shows imports, metadata, payload role index, CLI, and runner logic first.
- The dense payload blob remains available but collapsible.
- conalog key artifact comparison remains 8/8 pass.
