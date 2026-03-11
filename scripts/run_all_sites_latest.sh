#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=/opt/homebrew/opt/python@3.11/libexec/bin/python3
PATH=/opt/homebrew/opt/python@3.11/libexec/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

sites=(kernelog1 sinhyo gangui ktc_ess)

for site in "${sites[@]}"; do
  echo "[RUN] $site"
  "$PYTHON_BIN" research/prognostics/run_site_latest.py --site "$site" || exit 1
done

echo "[RUN] build_site_event_phenotypes"
"$PYTHON_BIN" research/prognostics/build_site_event_phenotypes.py || exit 1

echo "[RUN] publish_site_latest_phenotypes"
"$PYTHON_BIN" research/prognostics/publish_site_latest_phenotypes.py || exit 1

echo "[DONE] all sites completed"
