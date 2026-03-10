#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/pv_ae"
python3 panel_day_engine.py \
  --dir "$ROOT/data/kernelog1/raw" \
  --train-start 2025-01-01 --train-end 2025-02-28 \
  --eval-start 2025-03-01 --eval-end 2026-02-18 \
  --device cpu
