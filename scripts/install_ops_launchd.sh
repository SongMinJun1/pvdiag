#!/usr/bin/env bash
set -euo pipefail

HOUR=2
MINUTE=10

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hour)
      HOUR="$2"
      shift 2
      ;;
    --minute)
      MINUTE="$2"
      shift 2
      ;;
    *)
      echo "[ERROR] unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/pvdiag.run_all_sites_latest.plist"
SCRIPT_PATH="$ROOT/scripts/run_all_sites_latest_logged.sh"

mkdir -p "$PLIST_DIR"

cat >"$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>pvdiag.run_all_sites_latest</string>
  <key>ProgramArguments</key>
  <array>
    <string>$SCRIPT_PATH</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>RunAtLoad</key>
  <false/>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>$HOUR</integer>
    <key>Minute</key>
    <integer>$MINUTE</integer>
  </dict>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl enable "gui/$(id -u)/pvdiag.run_all_sites_latest" >/dev/null 2>&1 || true

echo "[OK] installed plist: $PLIST_PATH"
echo "[OK] schedule: $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
echo "[OK] command: $SCRIPT_PATH"
