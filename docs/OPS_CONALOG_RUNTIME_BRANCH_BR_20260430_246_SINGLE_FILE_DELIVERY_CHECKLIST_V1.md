<!-- markdownlint-disable MD013 -->

# BR-20260430-246 Single File Delivery Checklist

## Summary
- This branch step adds a concise internal checklist for the one-file professor handoff.
- The checklist states what to send, what not to send, package prerequisites, run commands, expected outputs, and failure triage.
- Runtime diagnosis semantics are unchanged.

## Added Artifact
- `release/conalog_full_runtime_v1/PVDIAG_SINGLE_DELIVERY_CHECKLIST.md`

## Checklist Boundary
- Professor-facing deliverable: `pvdiag_single.py` only.
- Internal support docs/checkers/manifests stay in the repo.
- Real CSVs and external Python packages are outside the generated file by design.

## Reproduction Command
```bash
python3 tools/check_pvdiag_single_delivery_closeout.py --export-output-dir /private/tmp/pvdiag_single_delivery_closeout_br247 --clean-output-dir
```

## Result
- The closeout checker verifies required checklist snippets before writing the release snapshot.
