<!-- markdownlint-disable MD013 -->

# BR-20260430-247 Single File Release Snapshot

## Summary
- This branch step writes a deterministic release snapshot for the current `pvdiag_single.py` delivery artifact.
- The snapshot records file size, SHA-256, embedded payload summary, external package prerequisites, expected result artifacts, and validation boundary.
- Runtime diagnosis semantics are unchanged.

## Added Artifact
- `release/conalog_full_runtime_v1/pvdiag_single_delivery_snapshot_v1.json`

## Why This Matters
- It answers "which exact file did we hand off?" without requiring a full runtime folder.
- It lets the user or professor verify the received file by checksum.
- It keeps the boundary clear: final truth-label evaluation still waits for real field-trial CSV and labels.

## Reproduction Commands
```bash
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_single_delivery_closeout_br247 --clean-output-dir
python3 /private/tmp/pvdiag_single_delivery_closeout_br247/pvdiag_single.py --single-self-test
```

## Result
- Closeout ready if `closeout_ready=1`, `professor_deliverable_file_count=1`, and `algorithm_semantics_changed=0`.
