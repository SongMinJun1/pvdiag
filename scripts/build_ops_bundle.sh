#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TMP=$ROOT/_ops_release_tmp
OUT=$TMP/pvdiag_ops_bundle
ZIP=$TMP/pvdiag_ops_bundle.zip

FILES=(
  "pv_ae/panel_day_engine.py"
  "research/prognostics/risk_score.py"
  "research/prognostics/add_transition_scores.py"
  "research/prognostics/add_ensemble_scores.py"
  "research/prognostics/run_scores_pipeline.py"
  "research/prognostics/run_panel_day_site.py"
  "research/prognostics/run_site_latest.py"
  "research/prognostics/ops_healthcheck.py"
  "scripts/run_all_sites_latest.sh"
  "scripts/run_all_sites_latest_logged.sh"
  "scripts/install_ops_launchd.sh"
  "scripts/uninstall_ops_launchd.sh"
  "configs/sites/conalog.yaml"
  "configs/sites/sinhyo.yaml"
  "configs/sites/gangui.yaml"
  "configs/sites/ktc_ess.yaml"
  "docs/OPS_RUNTIME.md"
  "docs/OPS_HANDOFF.md"
  "docs/OPS_SCHEDULE.md"
  "docs/OPS_DAILY_CHECKLIST.md"
  "docs/DATA_DICTIONARY.md"
  "requirements.txt"
)

rm -rf "$OUT"
mkdir -p "$OUT"
mkdir -p "$TMP"

for rel in "${FILES[@]}"; do
  src="$ROOT/$rel"
  dst="$OUT/$rel"
  if [[ ! -f "$src" ]]; then
    echo "[ERROR] missing required file: $src" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
done

rm -f "$ZIP"
(
  cd "$TMP"
  zip -r "pvdiag_ops_bundle.zip" "pvdiag_ops_bundle" >/dev/null
)

echo "[OPS BUNDLE FILES]"
for rel in "${FILES[@]}"; do
  echo "$rel"
done
echo

echo "[OPS BUNDLE ZIP]"
ls -lh "$ZIP"
