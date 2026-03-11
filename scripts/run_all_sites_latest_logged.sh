#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/_ops_runtime_logs"
mkdir -p "$LOG_DIR"

TS="$(date '+%Y%m%d_%H%M%S')"
LOG_PATH="$LOG_DIR/run_all_sites_latest_${TS}.log"
STATUS_PATH="$LOG_DIR/latest.status"
LATEST_LOG_PATH="$LOG_DIR/latest.log"

{
  echo "[INFO] started_at=$(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "[INFO] root=$ROOT"
  bash "$ROOT/scripts/run_all_sites_latest.sh"
} >"$LOG_PATH" 2>&1
RC=$?

cp "$LOG_PATH" "$LATEST_LOG_PATH"
{
  echo "timestamp=$TS"
  echo "exit_code=$RC"
  echo "log_file=$(basename "$LOG_PATH")"
} >"$STATUS_PATH"

exit "$RC"
