#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/pv_ae"

python3 pv_autoencoder_dayAE.py \
  --dir "$ROOT/data/gangui/raw" \
  --train-start 2025-04-10 --train-end 2025-08-31 \
  --eval-start 2025-09-01 --eval-end 2026-01-15 \
  --device cpu
