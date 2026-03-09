#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/pv_ae"
python3 panel_day_engine.py \
  --dir "$ROOT/data/ktc_ess/raw" \
  --train-start 2024-08-14 --train-end 2025-06-30 \
  --eval-start 2025-07-01 --eval-end 2026-01-15 \
  --device cpu
