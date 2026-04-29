<!-- markdownlint-disable MD013 -->

# BR-20260430-248 Single File Source Text Payload

## Summary
- This patch changes the generated `pvdiag_single.py` payload from zip/base64 to UTF-8 source-text.
- The professor-facing artifact remains one file.
- Runtime diagnosis semantics are unchanged.

## Why
- The previous generated file was technically correct, but the base64 block looked opaque when opened.
- This patch keeps the one-file handoff while making the embedded files visible as `EMBEDDED_TEXT_FILES`.
- The implementation still restores the original modular file tree in a temporary runtime directory before calling the existing runner.

## Guardrails
- `tools/check_pvdiag_single_handoff.py` fails if the generated file still contains `PAYLOAD_B64`, `import base64`, or `import zipfile`.
- `research/prognostics/smoke_test_pvdiag_single_delivery_v1.py` verifies the source-text payload markers.
- `tools/check_pvdiag_single_delivery_closeout.py` records `payload_mode=source_text` in the delivery snapshot.

## Reproduction Commands
```bash
python3 tools/build_pvdiag_single_py.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_single_source_text_br248 --clean-output-dir
python3 /private/tmp/pvdiag_single_source_text_br248/pvdiag_single.py --single-self-test
```

## Result Boundary
- One-file delivery remains intact.
- External packages and real CSV data remain external prerequisites.
- Truth-label performance evaluation still waits for real field-trial CSV and labels.
