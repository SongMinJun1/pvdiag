#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/pvdiag.run_all_sites_latest.plist"
LABEL="gui/$(id -u)/pvdiag.run_all_sites_latest"

launchctl bootout "$LABEL" >/dev/null 2>&1 || true
launchctl disable "$LABEL" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

echo "[OK] removed plist: $PLIST_PATH"
