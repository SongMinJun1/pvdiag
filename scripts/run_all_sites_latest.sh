#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

sites=(kernelog1 sinhyo gangui ktc_ess)

for site in "${sites[@]}"; do
  echo "[RUN] $site"
  python research/prognostics/run_site_latest.py --site "$site" || exit 1
done

echo "[DONE] all sites completed"
