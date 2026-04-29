<!-- markdownlint-disable MD013 -->

# BR-20260430-253 Single-File Payload Transparency

## Purpose
- BR-252 correctly reduced generated `pvdiag_single.py` line noise, but the JSON chunk container made the internal module structure hard to see.
- This branch keeps the non-base64/non-zip, compact generated artifact while making the embedded runtime explainable to a reviewer.

## Change
- Add visible `PAYLOAD_FILE_INDEX` to generated `pvdiag_single.py`.
  - Each payload row shows role, path, byte count, line count, and SHA-256.
- Add no-dependency inspection commands.
  - `python pvdiag_single.py --single-list-payload`
  - `python pvdiag_single.py --single-extract-source /tmp/pvdiag_single_source`
- Extend handoff/smoke/closeout checks so the single-file artifact must expose and validate this visible structure.

## Boundary
- No diagnostic algorithm semantics change.
- No `pv_ae/panel_day_engine.py` logic change.
- The payload remains source-text JSON chunks, not zip/base64.
- The essential payload count remains 11 files from the BR-252 omit audit.

## Why This Is Better
- The professor-facing file is still one file.
- The file is no longer a giant line-literal dump.
- A reviewer can see the embedded structure at the top of the file.
- A reviewer can unpack readable source files without needing the original repo.

## Validation Plan
```bash
python3 tools/build_pvdiag_single_py.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py research/prognostics/smoke_test_pvdiag_single_failure_ux_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br253_delivery --clean-output-dir
python3 /private/tmp/pvdiag_br253_delivery/pvdiag_single.py --single-list-payload
python3 /private/tmp/pvdiag_br253_delivery/pvdiag_single.py --single-extract-source /private/tmp/pvdiag_br253_source_extract
python3 /private/tmp/pvdiag_br253_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br253_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_br251_conalog --single-output-root /private/tmp/pvdiag_br253_conalog --json-output /private/tmp/pvdiag_br253_compare.json
```

## Expected Result
- `pvdiag_single.py` remains compact enough for handoff.
- `PAYLOAD_FILE_INDEX` makes the module/artifact boundary visible.
- `--single-extract-source` provides readable code structure when needed.
- conalog key artifact comparison remains 8/8 pass.
