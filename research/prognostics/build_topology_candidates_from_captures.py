#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
CAPTURE_KINDS = ["reports", "latest_state", "panelmaps", "plant", "inverter"]
SUMMARY_COLS = [
    "site",
    "reports_present",
    "latest_state_present",
    "panelmaps_present",
    "plant_present",
    "inverter_present",
    "reports_panel_count",
    "reports_inverter_count",
    "inventory_panel_count",
    "candidate_rows",
    "candidate_panel_count",
    "candidate_string_count",
    "candidate_mppt_count",
    "candidate_inverter_count",
    "strong_candidate_rows",
    "medium_candidate_rows",
    "weak_candidate_rows",
]
CANDIDATE_COLS = [
    "site",
    "panel_id",
    "candidate_string_id",
    "candidate_mppt_id",
    "candidate_inverter_id",
    "source_kind",
    "source_field_path",
    "source_strength",
    "note",
]
CONFLICT_COLS = [
    "site",
    "panel_id",
    "row_count",
    "string_values_seen",
    "mppt_values_seen",
    "inverter_values_seen",
    "source_kinds_seen",
]
MISSING_COLS = [
    "site",
    "missing_reports",
    "missing_latest_state",
    "missing_panelmaps",
    "missing_plant",
    "missing_inverter",
]
PANEL_KEY_ALIASES = ["panel_id", "panelid", "panelposition", "panel_position", "map_id", "mapid"]
GENERIC_ID_ALIASES = ["id"]
STRING_KEY_ALIASES = ["string", "string_id", "stringid"]
MPPT_KEY_ALIASES = ["mppt", "mppt_id", "mpptid"]
INVERTER_KEY_ALIASES = ["inverter", "inverter_id", "inverterid"]
AMBIGUOUS_KEY_ALIASES = ["channel", "channel_id", "channelid", "array", "array_id", "arrayid", "group", "group_id", "groupid"]
PANEL_COUNT_ALIASES = ["panelcount", "panel_count"]
INVERTER_COUNT_ALIASES = ["invertercount", "inverter_count"]
ADDRESS_ALIASES = ["address"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build topology candidates from saved webapp JSON captures.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    return parser.parse_args()


def normalize_key(key: str) -> str:
    return "".join(ch for ch in str(key).strip().lower() if ch.isalnum() or ch == "_")


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk_json(node: Any, path: str = "$") -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    if isinstance(node, dict):
        rows.append((path, node))
        for key, value in node.items():
            child_path = f"{path}.{key}"
            rows.extend(walk_json(value, child_path))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            child_path = f"{path}[{idx}]"
            rows.extend(walk_json(value, child_path))
    return rows


def extract_scalar(record: dict[str, Any], aliases: list[str]) -> tuple[str, str]:
    normalized = {normalize_key(key): key for key in record.keys()}
    for alias in aliases:
        if alias in normalized:
            real_key = normalized[alias]
            value = record.get(real_key)
            if isinstance(value, (dict, list)):
                continue
            text = normalize_text(value)
            if text:
                return text, real_key
    return "", ""


def path_suggests_panel(path: str) -> bool:
    lowered = path.lower()
    return any(token in lowered for token in ["panel", "map", "state", "metric"])


def extract_panel_id(record: dict[str, Any], path: str, allow_generic_id: bool) -> tuple[str, str]:
    explicit_value, explicit_key = extract_scalar(record, PANEL_KEY_ALIASES)
    if explicit_value:
        return explicit_value, explicit_key
    if allow_generic_id and path_suggests_panel(path):
        generic_value, generic_key = extract_scalar(record, GENERIC_ID_ALIASES)
        if generic_value:
            return generic_value, generic_key
    return "", ""


def strength_for_candidate(
    panel_id: str,
    string_id: str,
    mppt_id: str,
    inverter_id: str,
    has_ambiguous: bool,
    inventory_only: bool,
) -> str:
    if not panel_id:
        return "none"
    if string_id and mppt_id and inverter_id:
        return "high"
    if string_id or inverter_id:
        return "medium"
    if has_ambiguous or inventory_only:
        return "weak"
    return "none"


def build_candidate_note(source_kind: str, inventory_only: bool, ambiguous_fields: dict[str, str], address: str) -> str:
    notes: list[str] = []
    if inventory_only and source_kind == "latest_state":
        notes.append("inventory_only")
    if ambiguous_fields:
        notes.append(
            "ambiguous_fields:" + ",".join(f"{key}={value}" for key, value in sorted(ambiguous_fields.items()))
        )
    if address:
        notes.append(f"address={address}")
    return "|".join(notes)


def find_first_scalar(node: Any, aliases: list[str]) -> str:
    for path, record in walk_json(node):
        del path
        value, _ = extract_scalar(record, aliases)
        if value:
            return value
    return ""


def parse_reports_meta(site: str, payload: Any) -> dict[str, object]:
    panel_count = pd.to_numeric(find_first_scalar(payload, PANEL_COUNT_ALIASES), errors="coerce")
    inverter_count = pd.to_numeric(find_first_scalar(payload, INVERTER_COUNT_ALIASES), errors="coerce")
    address = find_first_scalar(payload, ADDRESS_ALIASES)
    return {
        "site": site,
        "reports_panel_count": panel_count,
        "reports_inverter_count": inverter_count,
        "address": address,
    }


def parse_inventory_panel_ids(payload: Any, source_kind: str) -> set[str]:
    panel_ids: set[str] = set()
    allow_generic_id = source_kind in {"latest_state", "panelmaps"}
    for path, record in walk_json(payload):
        panel_id, _ = extract_panel_id(record, path, allow_generic_id=allow_generic_id)
        if panel_id:
            panel_ids.add(panel_id)
    return panel_ids


def parse_candidate_rows(site: str, source_kind: str, payload: Any) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    allow_generic_id = source_kind in {"latest_state", "panelmaps", "plant", "inverter"}
    for path, record in walk_json(payload):
        panel_id, panel_key = extract_panel_id(record, path, allow_generic_id=allow_generic_id)
        if not panel_id:
            continue

        string_id, string_key = extract_scalar(record, STRING_KEY_ALIASES)
        mppt_id, mppt_key = extract_scalar(record, MPPT_KEY_ALIASES)
        inverter_id, inverter_key = extract_scalar(record, INVERTER_KEY_ALIASES)

        ambiguous_fields: dict[str, str] = {}
        normalized = {normalize_key(key): key for key in record.keys()}
        for alias in AMBIGUOUS_KEY_ALIASES:
            if alias in normalized:
                key = normalized[alias]
                value = normalize_text(record.get(key))
                if value:
                    ambiguous_fields[key] = value

        inventory_only = source_kind == "latest_state" and not (string_id or mppt_id or inverter_id or ambiguous_fields)
        source_strength = strength_for_candidate(
            panel_id=panel_id,
            string_id=string_id,
            mppt_id=mppt_id,
            inverter_id=inverter_id,
            has_ambiguous=bool(ambiguous_fields),
            inventory_only=inventory_only,
        )
        if source_strength == "none":
            continue

        field_names = [panel_key]
        for key in [string_key, mppt_key, inverter_key]:
            if key:
                field_names.append(key)
        field_names.extend(sorted(ambiguous_fields.keys()))
        note = build_candidate_note(
            source_kind=source_kind,
            inventory_only=inventory_only,
            ambiguous_fields=ambiguous_fields,
            address="",
        )
        rows.append(
            {
                "site": site,
                "panel_id": panel_id,
                "candidate_string_id": string_id,
                "candidate_mppt_id": mppt_id,
                "candidate_inverter_id": inverter_id,
                "source_kind": source_kind,
                "source_field_path": f"{path}::" + ",".join(field_names),
                "source_strength": source_strength,
                "note": note,
            }
        )
    return rows


def build_conflicts(candidates: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return pd.DataFrame(columns=CONFLICT_COLS)

    def join_distinct(values: pd.Series) -> str:
        cleaned = sorted({normalize_text(value) for value in values if normalize_text(value)})
        return "|".join(cleaned)

    grouped = (
        candidates.groupby(["site", "panel_id"], dropna=False)
        .agg(
            row_count=("panel_id", "size"),
            string_values_seen=("candidate_string_id", join_distinct),
            mppt_values_seen=("candidate_mppt_id", join_distinct),
            inverter_values_seen=("candidate_inverter_id", join_distinct),
            source_kinds_seen=("source_kind", join_distinct),
        )
        .reset_index()
    )
    conflict_mask = (
        grouped["string_values_seen"].str.contains(r"\|", regex=True, na=False)
        | grouped["mppt_values_seen"].str.contains(r"\|", regex=True, na=False)
        | grouped["inverter_values_seen"].str.contains(r"\|", regex=True, na=False)
    )
    conflicts = grouped.loc[conflict_mask, CONFLICT_COLS].copy()
    conflicts = conflicts.sort_values(["site", "panel_id"], kind="stable").reset_index(drop=True)
    return conflicts


def build_summary(
    reports_meta: pd.DataFrame,
    inventory_counts: pd.DataFrame,
    candidates: pd.DataFrame,
    missing_sources: pd.DataFrame,
) -> pd.DataFrame:
    reports_lookup = reports_meta.set_index("site").to_dict("index") if not reports_meta.empty else {}
    inventory_lookup = inventory_counts.set_index("site").to_dict("index") if not inventory_counts.empty else {}

    rows: list[dict[str, object]] = []
    for site in SITES:
        site_candidates = candidates.loc[candidates["site"].eq(site)].copy()
        report_row = reports_lookup.get(site, {})
        inventory_row = inventory_lookup.get(site, {})
        missing_row = missing_sources.loc[missing_sources["site"].eq(site)].iloc[0].to_dict()
        rows.append(
            {
                "site": site,
                "reports_present": 1 - int(missing_row["missing_reports"]),
                "latest_state_present": 1 - int(missing_row["missing_latest_state"]),
                "panelmaps_present": 1 - int(missing_row["missing_panelmaps"]),
                "plant_present": 1 - int(missing_row["missing_plant"]),
                "inverter_present": 1 - int(missing_row["missing_inverter"]),
                "reports_panel_count": report_row.get("reports_panel_count", pd.NA),
                "reports_inverter_count": report_row.get("reports_inverter_count", pd.NA),
                "inventory_panel_count": inventory_row.get("inventory_panel_count", 0),
                "candidate_rows": int(len(site_candidates)),
                "candidate_panel_count": int(site_candidates["panel_id"].nunique(dropna=True)),
                "candidate_string_count": int(site_candidates["candidate_string_id"].replace("", pd.NA).nunique(dropna=True)),
                "candidate_mppt_count": int(site_candidates["candidate_mppt_id"].replace("", pd.NA).nunique(dropna=True)),
                "candidate_inverter_count": int(site_candidates["candidate_inverter_id"].replace("", pd.NA).nunique(dropna=True)),
                "strong_candidate_rows": int(site_candidates["source_strength"].eq("high").sum()),
                "medium_candidate_rows": int(site_candidates["source_strength"].eq("medium").sum()),
                "weak_candidate_rows": int(site_candidates["source_strength"].eq("weak").sum()),
            }
        )

    summary = pd.DataFrame(rows)
    return summary[SUMMARY_COLS].copy()


def build_missing_sources(root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    capture_dir = root / "data" / "manual" / "webapp_captures"
    for site in SITES:
        row = {"site": site}
        for source_kind in CAPTURE_KINDS:
            row[f"missing_{source_kind}"] = int(not (capture_dir / f"{site}_{source_kind}.json").exists())
        rows.append(row)
    return pd.DataFrame(rows)[MISSING_COLS].copy()


def build_topology_candidates_from_captures(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    capture_dir = root / "data" / "manual" / "webapp_captures"
    reports_rows: list[dict[str, object]] = []
    inventory_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []

    for site in SITES:
        for source_kind in CAPTURE_KINDS:
            path = capture_dir / f"{site}_{source_kind}.json"
            if not path.exists():
                continue
            payload = read_json(path)

            if source_kind == "reports":
                reports_rows.append(parse_reports_meta(site, payload))

            if source_kind == "latest_state":
                inventory_panel_ids = parse_inventory_panel_ids(payload, source_kind)
                inventory_rows.append({"site": site, "inventory_panel_count": len(inventory_panel_ids)})

            if source_kind in {"latest_state", "panelmaps", "plant", "inverter"}:
                candidate_rows.extend(parse_candidate_rows(site, source_kind, payload))

    reports_meta = pd.DataFrame(reports_rows, columns=["site", "reports_panel_count", "reports_inverter_count", "address"])
    inventory_counts = pd.DataFrame(inventory_rows, columns=["site", "inventory_panel_count"])
    if inventory_counts.empty:
        inventory_counts = pd.DataFrame({"site": SITES, "inventory_panel_count": [0] * len(SITES)})
    else:
        inventory_counts = (
            inventory_counts.groupby("site", dropna=False)["inventory_panel_count"]
            .max()
            .reset_index()
        )

    candidates = pd.DataFrame(candidate_rows, columns=CANDIDATE_COLS)
    if not candidates.empty:
        for col in CANDIDATE_COLS:
            candidates[col] = candidates[col].fillna("").astype(str).str.strip()
        candidates = candidates.sort_values(["site", "panel_id", "source_kind", "source_field_path"], kind="stable").reset_index(drop=True)
    else:
        candidates = pd.DataFrame(columns=CANDIDATE_COLS)

    conflicts = build_conflicts(candidates)
    missing_sources = build_missing_sources(root)
    summary = build_summary(reports_meta, inventory_counts, candidates, missing_sources)
    return summary, candidates, conflicts, missing_sources


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    summary, candidates, conflicts, missing_sources = build_topology_candidates_from_captures(root)

    share_dir = root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(share_dir / "site_topology_capture_summary.csv", index=False, encoding="utf-8-sig")
    candidates.to_csv(share_dir / "site_topology_candidate_rows.csv", index=False, encoding="utf-8-sig")
    conflicts.to_csv(share_dir / "site_topology_candidate_conflicts.csv", index=False, encoding="utf-8-sig")
    missing_sources.to_csv(share_dir / "site_topology_missing_sources.csv", index=False, encoding="utf-8-sig")

    print(
        "built topology candidates from captures: "
        f"summary_rows={len(summary)}, candidate_rows={len(candidates)}, conflict_rows={len(conflicts)}"
    )


if __name__ == "__main__":
    main()
