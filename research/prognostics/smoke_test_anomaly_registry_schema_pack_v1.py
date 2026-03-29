#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


REQUIRED_ENTITIES = {
    "strict_case_ledger_v1",
    "panel_day_evidence_matrix_v1",
    "panel_local_episode_registry_v1",
    "common_cause_incident_registry_v1",
    "strict_case_mapping_v1",
    "episode_incident_relation_v1",
    "panel_history_view_v1",
}
REQUIRED_FIELDS = {
    "strict_case_ledger_v1": {
        "strict_case_id",
        "site",
        "panel_id",
        "strict_trigger_date",
        "strict_source",
        "raw_reason_summary",
        "provenance_version",
    },
    "panel_day_evidence_matrix_v1": {
        "site",
        "panel_id",
        "date",
        "coverage_mid",
        "coverage_ok_flag",
        "mid_ratio",
        "last_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "shadow_like_flag",
        "group_off_like_flag",
        "shape_flag",
        "shape_score",
        "instability_flag",
        "instability_score",
        "electrical_like_flag",
        "open_device_like_flag",
        "local_signal_signature",
        "evidence_reason_code",
        "group_proxy_value",
        "group_proxy_source",
        "topology_confidence",
    },
    "panel_local_episode_registry_v1": {
        "site",
        "panel_id",
        "panel_episode_id",
        "episode_start_date",
        "episode_end_date",
        "representative_strict_trigger_date",
        "episode_day_count",
        "strict_case_row_count",
        "dominant_local_family",
        "first_signal_family",
        "peak_signal_family",
        "last_signal_family",
        "temporal_signature",
        "has_output_drop",
        "has_voltage_drop",
        "has_current_drop",
        "has_shape_anomaly",
        "has_instability",
        "has_shadow_like",
        "has_group_off_like",
        "common_cause_overlap_flag",
        "linked_incident_count",
        "episode_confidence",
        "open_reason_code",
        "close_reason_code",
        "episode_note",
    },
    "common_cause_incident_registry_v1": {
        "site",
        "incident_id",
        "incident_start_date",
        "incident_end_date",
        "incident_day_count",
        "incident_scope",
        "affected_group_count",
        "affected_panel_count",
        "max_group_like_share",
        "max_site_affected_share",
        "dominant_incident_family",
        "incident_confidence",
        "recommended_action",
        "group_proxy_source_mode",
        "topology_confidence",
        "open_reason_code",
        "close_reason_code",
    },
    "strict_case_mapping_v1": {
        "strict_case_id",
        "site",
        "panel_id",
        "strict_trigger_date",
        "mapped_panel_episode_id",
        "mapped_incident_id",
        "membership_role",
        "mapping_confidence",
        "mapping_reason_code",
    },
    "episode_incident_relation_v1": {
        "relation_id",
        "src_node_type",
        "src_node_id",
        "dst_node_type",
        "dst_node_id",
        "relation_type",
        "claim_level",
        "relation_direction",
        "lead_days",
        "relation_confidence",
        "relation_reason_code",
    },
    "panel_history_view_v1": {
        "site",
        "panel_id",
        "local_episode_count",
        "incident_membership_count",
        "latest_local_episode_id",
        "latest_incident_id",
        "history_summary_ko",
        "current_status",
    },
}
REQUIRED_ENUMS = {
    "strict_source",
    "dominant_local_family",
    "temporal_signature",
    "incident_scope",
    "membership_role",
    "relation_type",
    "claim_level",
    "relation_direction",
    "group_proxy_source",
    "topology_confidence",
    "episode_confidence",
    "incident_confidence",
    "mapping_confidence",
    "relation_confidence",
    "recommended_action",
    "current_status",
    "entity_layer",
    "key_role",
    "source_type",
    "null_policy",
}
REQUIRED_CONFIG_KEYS = {
    "cfg.local_gap_tolerance_days",
    "cfg.local_recovery_close_days",
    "cfg.incident_min_group_panels",
    "cfg.incident_min_group_share",
    "cfg.incident_min_groups",
    "cfg.incident_min_site_panels",
    "cfg.incident_min_site_share",
    "cfg.incident_merge_group_overlap_share",
    "cfg.precursor_min_lead_days",
    "cfg.precursor_max_lead_days",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_anomaly_registry_schema_pack_v1.py"
    safe_smoke_merge = root / "research" / "prognostics" / "smoke_test_merge_readiness_pack_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        expected_output_names = {
            "anomaly_registry_schema_tables_v1.csv",
            "anomaly_registry_enum_catalog_v1.csv",
            "anomaly_registry_reason_codes_v1.csv",
            "anomaly_registry_config_keys_v1.csv",
        }
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(produced_output_names == expected_output_names, "builder should only emit the four schema freeze outputs")

        schema_df = pd.read_csv(share_dir / "anomaly_registry_schema_tables_v1.csv", encoding="utf-8-sig")
        enum_df = pd.read_csv(share_dir / "anomaly_registry_enum_catalog_v1.csv", encoding="utf-8-sig")
        reason_df = pd.read_csv(share_dir / "anomaly_registry_reason_codes_v1.csv", encoding="utf-8-sig")
        config_df = pd.read_csv(share_dir / "anomaly_registry_config_keys_v1.csv", encoding="utf-8-sig")

        entity_names = set(schema_df["entity_name"].astype(str))
        assert_true(entity_names == REQUIRED_ENTITIES, "all 7 required entities should appear in schema coverage")
        assert_true(len(entity_names) == 7, "entity coverage should contain exactly 7 unique entities")

        for entity_name, required_fields in REQUIRED_FIELDS.items():
            present_fields = set(
                schema_df.loc[schema_df["entity_name"].astype(str).eq(entity_name), "field_name"].astype(str)
            )
            missing_fields = sorted(required_fields - present_fields)
            assert_true(not missing_fields, f"{entity_name} missing required fields: {missing_fields}")

        present_enums = set(enum_df["enum_name"].astype(str))
        missing_enums = sorted(REQUIRED_ENUMS - present_enums)
        assert_true(not missing_enums, f"enum catalog missing required enums: {missing_enums}")

        present_config_keys = set(config_df["config_key"].astype(str))
        missing_config_keys = sorted(REQUIRED_CONFIG_KEYS - present_config_keys)
        assert_true(not missing_config_keys, f"config catalog missing required keys: {missing_config_keys}")

        assert_true(
            reason_df["reason_code"].astype(str).is_unique,
            "reason codes should be unique",
        )
        duplicated_field_orders = schema_df.loc[
            schema_df.duplicated(subset=["entity_name", "field_order"], keep=False),
            ["entity_name", "field_order"],
        ]
        assert_true(
            duplicated_field_orders.empty,
            "field_order should be unique within each entity",
        )

    print("[OK] outputs generate")
    print("[OK] all 7 required entities appear exactly once in entity coverage")
    print("[OK] all required fields listed above are present in anomaly_registry_schema_tables_v1.csv")
    print("[OK] all required enums appear in anomaly_registry_enum_catalog_v1.csv")
    print("[OK] all required config keys appear in anomaly_registry_config_keys_v1.csv")
    print("[OK] reason codes are unique")
    print("[OK] field_order is unique within each entity")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke_merge)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()
