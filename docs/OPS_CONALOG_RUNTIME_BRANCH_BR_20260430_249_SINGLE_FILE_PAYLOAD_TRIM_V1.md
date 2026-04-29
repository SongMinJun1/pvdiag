<!-- markdownlint-disable MD013 -->

# BR-20260430-249 Single File Payload Trim

## Summary
- This patch trims the generated `pvdiag_single.py` source-text payload from 24 files to 16 files.
- The professor-facing artifact remains one Python file.
- Runtime diagnosis semantics are unchanged.

## Removed From Single-File Payload
- `app/import_any_csv_root.py`
- `requirements.txt`
- `artifacts/ktc_fault2_label_and_algorithm_preview_v1.csv`
- `research/prognostics/build_panel_day_engine_bootstrap_verdict_v1.py`
- `research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py`
- `research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py`
- `research/prognostics/build_panel_day_engine_gpvs_evidence_pack_v1.py`
- `research/prognostics/build_panel_day_engine_cause_candidate_heuristics_v1.py`

## Rationale
- The single-file handoff accepts an already arranged `--data-root`; importer helper code is not used.
- Package metadata is not read at runtime.
- The KTC fault2 preview is a side preview artifact and is not copied/read by the one-file result path.
- Frozen-share live-chain builders cannot run in the one-file handoff because the required `package/_share` support assets are intentionally not embedded.
- The raw-only runtime chain remains embedded and validated.

## Reproduction Commands
```bash
python3 tools/build_pvdiag_single_py.py
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_single_payload_trim_br249 --clean-output-dir
python3 /private/tmp/pvdiag_single_payload_trim_br249/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_single_payload_trim_conalog_br249 --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_single_source_text_conalog_br248 --single-output-root /private/tmp/pvdiag_single_payload_trim_conalog_br249 --json-output /private/tmp/pvdiag_payload_trim_compare_br249.json
```

## Result
- payload files: 16
- payload mode: `source_text`
- key artifact compare: pass
- one-file delivery boundary: unchanged
