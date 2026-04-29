<!-- markdownlint-disable MD013 -->

# BR-20260430-255 Single-File Readable Payload

## Purpose
- BR-254 made the payload foldable, but the payload was still a compact `EMBEDDED_TEXT_JSON_CHUNKS` blob.
- For professor-facing delivery, the single file should be inspectable without decoding a JSON wall or trusting a hidden bundle.
- This branch prioritizes readability over the previous line-count diet while preserving the one-file runtime contract.

## Change
- Replace `EMBEDDED_TEXT_JSON_CHUNKS` with readable comment blocks:
  - `# pvdiag_payload_file {...}` records path, role, bytes, lines, SHA-256, and final-newline status.
  - `#|...` stores each original source line as a normal Python comment.
  - `# pvdiag_payload_end` closes each embedded file.
- Add runtime parsing that reads `pvdiag_single.py` itself, reconstructs the embedded source files, and then runs the same extracted modular runner.
- Keep `PAYLOAD_FILE_INDEX`, `--single-list-payload`, and `--single-extract-source`.
- Update handoff/closeout/smoke checks to reject JSON chunk payloads and require readable payload markers.

## Boundary
- No diagnostic algorithm semantics change.
- No payload necessity change: still 11 essential files.
- No base64, zip, or external generated sidecar.
- The generated file is longer, intentionally, so the embedded code is visible and auditable.

## Validation Plan
```bash
python3 tools/build_pvdiag_single_py.py
python3 release/conalog_full_runtime_v1/pvdiag_single.py --single-list-payload
python3 release/conalog_full_runtime_v1/pvdiag_single.py --single-extract-source /private/tmp/pvdiag_br255_source_extract_probe
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br255_delivery --clean-output-dir
python3 tools/export_pvdiag_single_delivery.py --output-dir /Users/b9gc/Desktop/pvdiag_professor_delivery --clean-output-dir
python3 /private/tmp/pvdiag_br255_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br255_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_br251_conalog --single-output-root /private/tmp/pvdiag_br255_conalog --json-output /private/tmp/pvdiag_br255_compare.json
```

## Expected Result
- `pvdiag_single.py` is still the only professor-facing file.
- Opening the file shows normal runner code first and a readable embedded payload region below.
- `--single-extract-source` restores byte/SHA-equivalent source files from the readable blocks.
- conalog key artifact comparison remains 8/8 pass.
