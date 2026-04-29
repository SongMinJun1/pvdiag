<!-- markdownlint-disable MD013 -->

# BR-20260430-250 Single File Fresh Handoff Repro

## Summary
- This branch verifies the professor-facing `pvdiag_single.py` from a fresh checkout of merged BR-249.
- No algorithm code or runtime semantics are changed.
- The check confirms that the repo artifact, exported one-file handoff, and Desktop delivery copy can be aligned to the same checksum.

## Fresh Checkout Boundary
- source branch: `origin/codex/final-delivery-runtime-lfs-base`
- fresh worktree: `/private/tmp/pvdiag_br250_fresh_handoff_repro`
- checked merge commit: `21e5e42541a128f66dbb532f46d78bd072ec83da`
- main dirty worktree was not used for edits.

## Reproduction Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py tools/build_pvdiag_single_py.py tools/check_pvdiag_single_handoff.py tools/check_pvdiag_single_delivery_closeout.py research/prognostics/smoke_test_pvdiag_single_delivery_v1.py research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py release/conalog_full_runtime_v1/pvdiag_single.py
python3 tools/build_pvdiag_single_py.py --output /private/tmp/pvdiag_br250_fresh_generated/pvdiag_single.py --manifest-output /private/tmp/pvdiag_br250_fresh_generated/pvdiag_single_manifest_v1.json
python3 /private/tmp/pvdiag_br250_fresh_generated/pvdiag_single.py --single-self-test
python3 tools/check_pvdiag_single_handoff.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_v1.py
python3 research/prognostics/smoke_test_pvdiag_single_delivery_export_v1.py
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_br250_fresh_delivery --snapshot-output /private/tmp/pvdiag_br250_fresh_snapshot.json --clean-output-dir
python3 /private/tmp/pvdiag_br250_fresh_delivery/pvdiag_single.py --single-self-test
python3 tools/export_pvdiag_single_delivery.py --output-dir /Users/b9gc/Desktop/pvdiag_professor_delivery --clean-output-dir
python3 /Users/b9gc/Desktop/pvdiag_professor_delivery/pvdiag_single.py --single-self-test
python3 /Users/b9gc/Desktop/pvdiag_professor_delivery/pvdiag_single.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/pvdiag_br250_desktop_conalog --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data --sites conalog
python3 tools/compare_pvdiag_single_results.py --modular-output-root /private/tmp/pvdiag_single_payload_trim_conalog_br249_final --single-output-root /private/tmp/pvdiag_br250_desktop_conalog --json-output /private/tmp/pvdiag_br250_fresh_compare.json
```

## Result
- payload mode: `source_text`
- payload files: 16
- payload text bytes: 432286
- excluded single-file payload entries: 8
- fresh exported file count: 1
- repo/export/Desktop SHA-256: `1ea231ca8f22149b6e9e1ae69f85df20bbcf23b079eb54dc59d194c57535601d`
- single file bytes: 561006
- Desktop self-test: pass
- Desktop conalog run: pass
- key artifact comparison: 8/8 pass

## Delivery Note
- The Desktop handoff folder is `/Users/b9gc/Desktop/pvdiag_professor_delivery`.
- It contains exactly `pvdiag_single.py`.
- The Desktop copy was refreshed during this audit because a prior intermediate export had a different generated timestamp checksum.
- This checksum difference was not a semantic difference, but aligning the Desktop copy with the merged branch avoids handoff ambiguity.

## Next Step
- Optional hardening: failure-message UX audit for missing packages, missing `data/`, invalid `--data-root`, and Jupyter/terminal use.
- Field-trial truth-label evaluation remains blocked until real KTC ESS CSV and final labels arrive.
