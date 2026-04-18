#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKFILL_SCRIPT = REPO_ROOT / "research/prognostics/build_panel_day_engine_historical_backfill_v1.py"


def load_backfill_module():
    spec = importlib.util.spec_from_file_location(
        "panel_day_engine_historical_backfill_v1",
        BACKFILL_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise SystemExit(f"failed to load backfill module: {BACKFILL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_backfill_module()
    return int(module.main(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
