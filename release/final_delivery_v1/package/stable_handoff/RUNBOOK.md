# Runbook

## 1. Dry-Run First
```bash
python app/run_conalog_infer.py \
  --dry-run \
  --input-root delivery/conalog_handoff_v1/examples \
  --output-root /tmp/conalog_handoff_dryrun \
  --config delivery/conalog_handoff_v1/config/default.yaml \
  --include-experimental off
```

## 2. Stable Run
```bash
python app/run_conalog_infer.py \
  --input-root delivery/conalog_handoff_v1/examples \
  --output-root /tmp/conalog_handoff_run \
  --config delivery/conalog_handoff_v1/config/default.yaml \
  --include-experimental off
```

## 3. Experimental Sidecar Run
```bash
python app/run_conalog_infer.py \
  --input-root delivery/conalog_handoff_v1/examples \
  --output-root /tmp/conalog_handoff_run_ref \
  --config delivery/conalog_handoff_v1/config/default.yaml \
  --include-experimental on
```

## 4. Reading Outputs
- 기본 전달은 stable output 기준으로 읽음.
- GPVS/heuristic sidecar 는 reference/triage 참고층으로만 읽음.
