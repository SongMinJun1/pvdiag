#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import py_compile
import tempfile
from pathlib import Path


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    engine_path = root / "pv_ae" / "panel_day_engine.py"
    spec = importlib.util.spec_from_file_location("panel_day_engine", engine_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"failed to import panel_day_engine from {engine_path}")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    py_compile.compile(str(engine_path), doraise=True)

    sample_pid = "550e8400-e29b-41d4-a716-446655440000.3.7"
    expected_heuristic = "550e8400-e29b-41d4-a716-446655440000.3"
    assert_true(engine.panel_group_key(sample_pid) == expected_heuristic, "default panel_group_key must keep heuristic behavior")
    assert_true(
        engine.panel_group_key(sample_pid, topology_map=None, grouping="heuristic") == expected_heuristic,
        "heuristic grouping with no topology must match legacy behavior",
    )
    assert_true(
        engine.panel_group_key(sample_pid, topology_map=None, grouping="string") == expected_heuristic,
        "missing topology must fall back to heuristic behavior",
    )

    with tempfile.TemporaryDirectory() as td:
        topo_path = Path(td) / "synthetic_topology.csv"
        write_csv(
            topo_path,
            ["panel_id", "string", "mppt", "inverter_id"],
            [
                [sample_pid, "S-01", "M-02", "INV-A"],
                ["550e8400-e29b-41d4-a716-446655440001.4.2", "S-01", "M-03", "INV-A"],
            ],
        )
        topo = engine.load_topology_map(str(topo_path))

        assert_true(engine.panel_group_key(sample_pid, topo, "string") == "S-01", "string grouping must use topology string_id")
        assert_true(engine.panel_group_key(sample_pid, topo, "mppt") == "M-02", "mppt grouping must use topology mppt_id")
        assert_true(engine.panel_group_key(sample_pid, topo, "inverter") == "INV-A", "inverter grouping must use topology inverter_id")

        missing_pid = "550e8400-e29b-41d4-a716-446655440099.9.9"
        assert_true(
            engine.panel_group_key(missing_pid, topo, "string") == engine.panel_group_key(missing_pid),
            "panels missing from topology must fall back to heuristic grouping",
        )

    print("[OK] panel_group_key heuristic compatibility verified")
    print("[OK] topology-aware string/mppt/inverter grouping verified")
    print("[OK] missing topology fallback verified")
    print("[OK] panel_day_engine.py compiles")


if __name__ == "__main__":
    main()
