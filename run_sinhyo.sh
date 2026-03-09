#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/pv_ae"
python3 panel_day_engine.py \
  --dir "$ROOT/data/sinhyo/raw" \
  --train-start 2025-01-01 --train-end 2025-06-30 \
  --eval-start 2025-07-01 --eval-end 2025-09-30 \
  --device cpu
