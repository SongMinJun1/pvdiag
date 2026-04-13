#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLS = ["site", "panel_id", "strict_trigger_date"]
DATE_JOIN_COLS = ["site", "strict_trigger_date"]
SITES = ["conalog", "gangui", "ktc_ess", "sinhyo"]
EVIDENCE_PACK_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "round1_review_order",
    "round1_bucket_rank",
    "review_priority_bucket",
    "priority_score",
    "review_focus",
    "recommended_review_action",
    "review_checklist",
    "vendor_reply_class",
    "vendor_fault_family",
    "critical_phenotype_v3",
    "actionability_v3",
    "official_error_modes",
    "official_error_types",
    "prediction_source",
    "official_truth_modes_if_present",
    "official_prediction_modes_if_present",
    "official_prediction_source_if_present",
    "anchor_date",
    "cluster_guard_flag",
    "critical_phenotype_v2",
    "current_critical_phenotype_v3",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
    "site_recommendation",
    "forensic_hypothesis",
    "include_in_site_specific_note_flag",
    "candidate_validity_review_axis",
    "date_judgement_review_axis",
    "evidence_summary_ko",
    "review_question_ko",
    "recommended_sources_ko",
    "review_priority",
    "note",
    "vendor_note",
]
SITE_PACKET_COLS = [
    "site",
    "review_priority_bucket",
    "case_count",
    "top_priority_score",
    "example_panel_ids",
    "dominant_review_focus",
    "packet_summary_ko",
]
CASE_PROMPT_COLS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "round1_review_order",
    "review_focus",
    "candidate_validity_review_axis",
    "date_judgement_review_axis",
    "review_question_ko",
    "recommended_sources_ko",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a reviewer-facing evidence pack for the round-1 manual truth review batch."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to project root.",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        default=SITES,
        help="Sites to include. Defaults to stable known sites.",
    )
    return parser.parse_args()


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def normalize_date(value: object) -> str:
    text = normalize_text(value)
    return text[:10] if len(text) >= 10 else text


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing input: {path}")
    return pd.read_csv(path, low_memory=False, encoding="utf-8-sig")


def first_nonblank(series: pd.Series) -> object:
    for value in series.tolist():
        if normalize_text(value):
            return value
    if series.dtype.kind in {"f", "i", "u"}:
        return float("nan")
    return ""


def aggregate_priority_cases(priority_df: pd.DataFrame) -> pd.DataFrame:
    if priority_df.empty:
        return pd.DataFrame(columns=[*KEY_COLS, "note", "vendor_note", "critical_phenotype_v3", "actionability_v3"])
    cols = [
        "note",
        "vendor_note",
        "critical_phenotype_v3",
        "actionability_v3",
        "vendor_reply_class",
        "vendor_fault_family",
    ]
    for col in cols:
        if col not in priority_df.columns:
            priority_df[col] = ""
        priority_df[col] = priority_df[col].map(normalize_text)
    return (
        priority_df.loc[:, [*KEY_COLS, *cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg({col: first_nonblank for col in cols})
    )


def aggregate_actionability(actionability_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["anchor_date", "cluster_guard_flag", "critical_phenotype_v2", "critical_phenotype_v3"]
    for col in cols:
        if col not in actionability_df.columns:
            actionability_df[col] = ""
    actionability_df["anchor_date"] = actionability_df["anchor_date"].map(normalize_date)
    actionability_df["critical_phenotype_v2"] = actionability_df["critical_phenotype_v2"].map(normalize_text)
    actionability_df["critical_phenotype_v3"] = actionability_df["critical_phenotype_v3"].map(normalize_text)
    actionability_df["cluster_guard_flag"] = pd.to_numeric(
        actionability_df["cluster_guard_flag"], errors="coerce"
    ).fillna(0).astype(int)
    aggregated = (
        actionability_df.loc[:, [*KEY_COLS, *cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            anchor_date=("anchor_date", first_nonblank),
            cluster_guard_flag=("cluster_guard_flag", "max"),
            critical_phenotype_v2=("critical_phenotype_v2", first_nonblank),
            current_critical_phenotype_v3=("critical_phenotype_v3", first_nonblank),
        )
    )
    return aggregated


def aggregate_onset(onset_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "first_warning_date",
        "retrospective_onset_date",
        "days_earlier_than_trigger",
        "onset_confidence",
        "onset_method",
        "reason_summary",
    ]
    for col in cols:
        if col not in onset_df.columns:
            onset_df[col] = ""
    onset_df["first_warning_date"] = onset_df["first_warning_date"].map(normalize_date)
    onset_df["retrospective_onset_date"] = onset_df["retrospective_onset_date"].map(normalize_date)
    onset_df["onset_confidence"] = onset_df["onset_confidence"].map(normalize_text)
    onset_df["onset_method"] = onset_df["onset_method"].map(normalize_text)
    onset_df["reason_summary"] = onset_df["reason_summary"].map(normalize_text)
    onset_df["days_earlier_than_trigger"] = pd.to_numeric(onset_df["days_earlier_than_trigger"], errors="coerce")
    return (
        onset_df.loc[:, [*KEY_COLS, *cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            first_warning_date=("first_warning_date", first_nonblank),
            retrospective_onset_date=("retrospective_onset_date", first_nonblank),
            days_earlier_than_trigger=("days_earlier_than_trigger", "max"),
            onset_confidence=("onset_confidence", first_nonblank),
            onset_method=("onset_method", first_nonblank),
            reason_summary=("reason_summary", first_nonblank),
        )
    )


def aggregate_errors(errors_df: pd.DataFrame) -> pd.DataFrame:
    filtered = errors_df.loc[errors_df["source_split"].map(normalize_text).eq("overall")].copy()
    if filtered.empty:
        return pd.DataFrame(
            columns=[
                *KEY_COLS,
                "official_truth_modes_if_present",
                "official_prediction_modes_if_present",
                "official_error_types_if_present",
                "official_prediction_source_if_present",
            ]
        )

    rows: list[dict[str, object]] = []
    for key, group in filtered.groupby(KEY_COLS, dropna=False):
        truth_modes = sorted({normalize_text(v) for v in group["truth_mode"] if normalize_text(v)})
        prediction_modes = sorted({normalize_text(v) for v in group["prediction_mode"] if normalize_text(v)})
        error_types = sorted({normalize_text(v) for v in group["error_type"] if normalize_text(v)})
        prediction_sources = sorted({normalize_text(v) for v in group["prediction_source"] if normalize_text(v)})
        rows.append(
            {
                "site": key[0],
                "panel_id": key[1],
                "strict_trigger_date": key[2],
                "official_truth_modes_if_present": "|".join(truth_modes),
                "official_prediction_modes_if_present": "|".join(prediction_modes),
                "official_error_types_if_present": "|".join(error_types),
                "official_prediction_source_if_present": "|".join(prediction_sources),
            }
        )
    return pd.DataFrame(rows)


def aggregate_vendor(vendor_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["vendor_reply_class", "vendor_fault_family", "vendor_note"]
    for col in cols:
        if col not in vendor_df.columns:
            vendor_df[col] = ""
        vendor_df[col] = vendor_df[col].map(normalize_text)
    return (
        vendor_df.loc[:, [*KEY_COLS, *cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            vendor_reply_class=("vendor_reply_class", first_nonblank),
            vendor_fault_family=("vendor_fault_family", first_nonblank),
            vendor_note=("vendor_note", first_nonblank),
        )
    )


def aggregate_precursor(precursor_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["site_recommendation", "forensic_hypothesis", "include_in_site_specific_note_flag"]
    for col in cols:
        if col not in precursor_df.columns:
            precursor_df[col] = ""
    precursor_df["site_recommendation"] = precursor_df["site_recommendation"].map(normalize_text)
    precursor_df["forensic_hypothesis"] = precursor_df["forensic_hypothesis"].map(normalize_text)
    precursor_df["include_in_site_specific_note_flag"] = pd.to_numeric(
        precursor_df["include_in_site_specific_note_flag"], errors="coerce"
    ).fillna(0).astype(int)
    precursor_df = precursor_df.rename(columns={"date": "strict_trigger_date"})
    return (
        precursor_df.loc[:, ["site", "strict_trigger_date", *cols]]
        .groupby(DATE_JOIN_COLS, as_index=False)
        .agg(
            site_recommendation=("site_recommendation", first_nonblank),
            forensic_hypothesis=("forensic_hypothesis", first_nonblank),
            include_in_site_specific_note_flag=("include_in_site_specific_note_flag", "max"),
        )
    )


def has_onset_context(row: pd.Series) -> bool:
    if normalize_text(row.get("first_warning_date", "")):
        return True
    if normalize_text(row.get("retrospective_onset_date", "")):
        return True
    if normalize_text(row.get("onset_confidence", "")):
        return True
    if normalize_text(row.get("onset_method", "")):
        return True
    if normalize_text(row.get("reason_summary", "")):
        return True
    value = pd.to_numeric(row.get("days_earlier_than_trigger", pd.NA), errors="coerce")
    return not pd.isna(value)


def build_review_axes(row: pd.Series) -> tuple[str, str]:
    review_focus = normalize_text(row["review_focus"])
    onset_available = has_onset_context(row)
    if review_focus == "official_error_reaudit":
        return (
            "panel_issue_vs_group_side_vs_false_positive",
            "strict_trigger_vs_onset_context" if onset_available else "strict_trigger_only",
        )
    if review_focus == "vendor_field_log_compare":
        return ("vendor_log_reconcile", "strict_trigger_only")
    return (
        "actionability_consistency",
        "strict_trigger_vs_onset_context" if onset_available else "strict_trigger_only",
    )


def format_onset_context(row: pd.Series) -> str:
    days = pd.to_numeric(row.get("days_earlier_than_trigger", pd.NA), errors="coerce")
    onset_confidence = normalize_text(row.get("onset_confidence", ""))
    onset_method = normalize_text(row.get("onset_method", ""))
    if pd.isna(days) and not onset_confidence and not onset_method:
        return "onset 추가 맥락 없음"
    parts: list[str] = []
    if not pd.isna(days):
        parts.append(f"트리거보다 {int(days)}일 선행")
    if onset_confidence:
        parts.append(f"신뢰도 {onset_confidence}")
    if onset_method:
        parts.append(f"방식 {onset_method}")
    return ", ".join(parts)


def build_evidence_summary_ko(row: pd.Series) -> str:
    review_focus = normalize_text(row["review_focus"])
    vendor_reply_class = normalize_text(row["vendor_reply_class"])
    vendor_fault_family = normalize_text(row["vendor_fault_family"])
    phenotype = normalize_text(row["critical_phenotype_v3"])
    actionability = normalize_text(row["actionability_v3"])
    official_modes = normalize_text(row["official_error_modes"])
    official_types = normalize_text(row["official_error_types"])
    onset_context = format_onset_context(row)
    critical_v2 = normalize_text(row.get("critical_phenotype_v2", ""))
    cluster_guard_flag = int(pd.to_numeric(row.get("cluster_guard_flag", 0), errors="coerce") or 0)
    site_recommendation = normalize_text(row.get("site_recommendation", ""))

    if review_focus == "official_error_reaudit":
        vendor_text = f"vendor는 {vendor_reply_class}/{vendor_fault_family} 맥락입니다." if vendor_reply_class or vendor_fault_family else "vendor 맥락은 비어 있습니다."
        return (
            f"공식 오류 맥락은 {official_modes or '없음'} / {official_types or '없음'}이며 "
            f"현재 phenotype/actionability는 {phenotype or '-'} / {actionability or '-'}입니다. "
            f"{vendor_text} {onset_context}."
        )
    if review_focus == "vendor_field_log_compare":
        return (
            f"vendor 회신은 {vendor_reply_class or '-'} / {vendor_fault_family or '-'}이고 "
            f"현재 actionability는 {actionability or '-'}입니다. "
            f"현장 로그와 vendor 설명이 실제 panel 문제인지 확인이 필요합니다."
        )
    cluster_text = "cluster/common-cause 맥락 있음" if cluster_guard_flag == 1 or site_recommendation else "뚜렷한 cluster guard 없음"
    return (
        f"현재 phenotype/actionability는 {phenotype or '-'} / {actionability or '-'}이며 "
        f"v2 phenotype은 {critical_v2 or '-'}입니다. {onset_context}, {cluster_text}."
    )


def build_review_question_ko(row: pd.Series) -> str:
    review_focus = normalize_text(row["review_focus"])
    if review_focus == "official_error_reaudit":
        return "이 strict case를 true_positive / group_side / false_positive 중 무엇으로 봐야 하는지와 strict_trigger_date가 타당한지 확인해 주세요."
    if review_focus == "vendor_field_log_compare":
        return "vendor 회신과 현장/O&M 로그를 대조했을 때 candidate_validity를 어떻게 입력해야 하는지 확인해 주세요."
    return "현재 phenotype/actionability 해석이 실제 유지보수 후보인지 리뷰 유지가 맞는지, 그리고 strict trigger 시점이 onset 맥락과 맞는지 확인해 주세요."


def build_recommended_sources_ko(row: pd.Series) -> str:
    review_focus = normalize_text(row["review_focus"])
    vendor_note = normalize_text(row["vendor_note"])
    note = normalize_text(row["note"])
    reason_summary = normalize_text(row.get("reason_summary", ""))
    if review_focus == "official_error_reaudit":
        extras = [text for text in [note, vendor_note] if text]
        extra_text = " / ".join(extras) if extras else "기존 메모 없음"
        return f"기존 review note, vendor note, field/O&M 로그를 먼저 보고 필요하면 onset reason({reason_summary or '-'})를 같이 확인하세요. 현재 메모: {extra_text}."
    if review_focus == "vendor_field_log_compare":
        return f"vendor note, field/O&M 로그, panel trend 맥락을 함께 보세요. vendor 메모: {vendor_note or '-'}."
    return (
        f"phenotype/actionability 출력, onset context, site cluster/common-cause 맥락을 함께 보세요. "
        f"기존 note: {note or '-'}, onset reason: {reason_summary or '-'}."
    )


def build_packet_summary_ko(site: str, bucket: str, case_count: int, review_focus: str) -> str:
    if review_focus == "official_error_reaudit":
        return f"{site} {bucket} {case_count}건: 공식 오류 맥락과 기존 메모를 먼저 대조하고 candidate_validity/date_judgement를 우선 결정하세요."
    if review_focus == "vendor_field_log_compare":
        return f"{site} {bucket} {case_count}건: vendor 회신과 field/O&M 로그의 일치 여부부터 확인한 뒤 candidate_validity를 정리하세요."
    return f"{site} {bucket} {case_count}건: phenotype/actionability와 onset 맥락이 유지보수 후보 해석과 맞는지 먼저 확인하세요."


def build_site_packets(evidence_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (site, bucket), group in evidence_df.groupby(["site", "review_priority_bucket"], dropna=False):
        ranked = group.sort_values(["priority_score", "round1_review_order"], ascending=[False, True]).reset_index(drop=True)
        dominant_review_focus = normalize_text(ranked.iloc[0]["review_focus"])
        rows.append(
            {
                "site": site,
                "review_priority_bucket": bucket,
                "case_count": int(len(group)),
                "top_priority_score": int(pd.to_numeric(group["priority_score"], errors="coerce").fillna(0).max()),
                "example_panel_ids": "|".join(ranked["panel_id"].map(normalize_text).drop_duplicates().head(3).tolist()),
                "dominant_review_focus": dominant_review_focus,
                "packet_summary_ko": build_packet_summary_ko(site, bucket, len(group), dominant_review_focus),
            }
        )
    packets_df = pd.DataFrame(rows, columns=SITE_PACKET_COLS)
    if packets_df.empty:
        return packets_df
    return packets_df.sort_values(
        ["site", "top_priority_score", "case_count", "review_priority_bucket"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)


def build_outputs(root: Path, sites: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    batch_df = read_csv(root / "_share" / "truth_review_batch_v1.csv")
    priority_df = read_csv(root / "_share" / "truth_coverage_priority_cases_v1.csv")
    actionability_df = read_csv(root / "_share" / "critical_actionability_shadow_v3_latest.csv")
    onset_df = read_csv(root / "_share" / "panel_onset_shadow_latest.csv")
    errors_df = read_csv(root / "_share" / "full_algorithm_case_errors_v3.csv")
    vendor_df = read_csv(root / "_share" / "vendor_reply_adjudication_latest.csv")
    precursor_df = read_csv(root / "_share" / "common_cause_precursor_decision_cases_v1.csv")

    for df in [batch_df, priority_df, actionability_df, onset_df, errors_df, vendor_df]:
        for col in KEY_COLS:
            if col not in df.columns:
                raise SystemExit(f"missing required column: {col}")
            if col == "strict_trigger_date":
                df[col] = df[col].map(normalize_date)
            else:
                df[col] = df[col].map(normalize_text)
    if "date" in precursor_df.columns:
        precursor_df["date"] = precursor_df["date"].map(normalize_date)
        precursor_df["site"] = precursor_df["site"].map(normalize_text)

    batch_df = batch_df.loc[batch_df["site"].isin(sites)].copy()
    if batch_df.empty:
        raise SystemExit("truth_review_batch_v1.csv produced an empty evidence-pack universe")

    base_cols = [
        "round1_review_order",
        "round1_bucket_rank",
        "review_priority_bucket",
        "priority_score",
        "review_focus",
        "recommended_review_action",
        "review_checklist",
        "vendor_reply_class",
        "vendor_fault_family",
        "critical_phenotype_v3",
        "actionability_v3",
        "official_error_modes",
        "official_error_types",
        "prediction_source",
        "gap_bucket",
        "promotion_hypothesis",
        "review_priority",
        "note",
        "vendor_note",
    ]
    for col in base_cols:
        if col not in batch_df.columns:
            batch_df[col] = ""
    for col in base_cols:
        if col in {"round1_review_order", "round1_bucket_rank", "priority_score"}:
            batch_df[col] = pd.to_numeric(batch_df[col], errors="coerce").fillna(0).astype(int)
        else:
            batch_df[col] = batch_df[col].map(normalize_text)
    batch_df = (
        batch_df.loc[:, [*KEY_COLS, *base_cols]]
        .groupby(KEY_COLS, as_index=False)
        .agg(
            round1_review_order=("round1_review_order", "min"),
            round1_bucket_rank=("round1_bucket_rank", "min"),
            review_priority_bucket=("review_priority_bucket", first_nonblank),
            priority_score=("priority_score", "max"),
            review_focus=("review_focus", first_nonblank),
            recommended_review_action=("recommended_review_action", first_nonblank),
            review_checklist=("review_checklist", first_nonblank),
            vendor_reply_class=("vendor_reply_class", first_nonblank),
            vendor_fault_family=("vendor_fault_family", first_nonblank),
            critical_phenotype_v3=("critical_phenotype_v3", first_nonblank),
            actionability_v3=("actionability_v3", first_nonblank),
            official_error_modes=("official_error_modes", first_nonblank),
            official_error_types=("official_error_types", first_nonblank),
            prediction_source=("prediction_source", first_nonblank),
            gap_bucket=("gap_bucket", first_nonblank),
            promotion_hypothesis=("promotion_hypothesis", first_nonblank),
            review_priority=("review_priority", first_nonblank),
            note=("note", first_nonblank),
            vendor_note=("vendor_note", first_nonblank),
        )
        .sort_values(["round1_review_order", "site", "strict_trigger_date", "panel_id"], ascending=[True, True, True, True])
        .reset_index(drop=True)
    )

    fallback_priority = aggregate_priority_cases(priority_df)
    actionability_context = aggregate_actionability(actionability_df)
    onset_context = aggregate_onset(onset_df)
    error_context = aggregate_errors(errors_df)
    vendor_context = aggregate_vendor(vendor_df)
    precursor_context = aggregate_precursor(precursor_df)

    evidence_df = (
        batch_df
        .merge(fallback_priority, on=KEY_COLS, how="left", suffixes=("", "_fallback"))
        .merge(actionability_context, on=KEY_COLS, how="left")
        .merge(onset_context, on=KEY_COLS, how="left")
        .merge(error_context, on=KEY_COLS, how="left")
        .merge(vendor_context, on=KEY_COLS, how="left", suffixes=("", "_vendor"))
        .merge(precursor_context, on=DATE_JOIN_COLS, how="left")
    )

    for col in [
        "anchor_date",
        "critical_phenotype_v2",
        "current_critical_phenotype_v3",
        "first_warning_date",
        "retrospective_onset_date",
        "onset_confidence",
        "onset_method",
        "reason_summary",
        "official_truth_modes_if_present",
        "official_prediction_modes_if_present",
        "official_error_types_if_present",
        "official_prediction_source_if_present",
        "site_recommendation",
        "forensic_hypothesis",
    ]:
        if col not in evidence_df.columns:
            evidence_df[col] = ""
        evidence_df[col] = evidence_df[col].map(normalize_text)

    for col in ["cluster_guard_flag", "include_in_site_specific_note_flag"]:
        if col not in evidence_df.columns:
            evidence_df[col] = 0
        evidence_df[col] = pd.to_numeric(evidence_df[col], errors="coerce").fillna(0).astype(int)

    evidence_df["days_earlier_than_trigger"] = pd.to_numeric(
        evidence_df.get("days_earlier_than_trigger", pd.Series(dtype=float)), errors="coerce"
    )

    for col in ["vendor_reply_class", "vendor_fault_family", "vendor_note"]:
        fallback_col = f"{col}_vendor"
        if fallback_col not in evidence_df.columns:
            evidence_df[fallback_col] = ""
        evidence_df[fallback_col] = evidence_df[fallback_col].map(normalize_text)
        evidence_df[col] = evidence_df[col].map(normalize_text)
        evidence_df[col] = evidence_df.apply(
            lambda row, primary=col, fallback=fallback_col: normalize_text(row[primary]) or normalize_text(row[fallback]),
            axis=1,
        )

    for col in ["note", "critical_phenotype_v3", "actionability_v3"]:
        fallback_col = f"{col}_fallback"
        if fallback_col not in evidence_df.columns:
            evidence_df[fallback_col] = ""
        evidence_df[fallback_col] = evidence_df[fallback_col].map(normalize_text)
        evidence_df[col] = evidence_df[col].map(normalize_text)
        evidence_df[col] = evidence_df.apply(
            lambda row, primary=col, fallback=fallback_col: normalize_text(row[primary]) or normalize_text(row[fallback]),
            axis=1,
        )

    evidence_df["official_error_modes"] = evidence_df.apply(
        lambda row: normalize_text(row["official_error_modes"])
        or (
            f"{normalize_text(row['official_truth_modes_if_present'])}:{normalize_text(row['official_prediction_modes_if_present'])}"
            if normalize_text(row["official_truth_modes_if_present"]) or normalize_text(row["official_prediction_modes_if_present"])
            else ""
        ),
        axis=1,
    )
    evidence_df["official_error_types"] = evidence_df.apply(
        lambda row: normalize_text(row["official_error_types"]) or normalize_text(row["official_error_types_if_present"]),
        axis=1,
    )
    evidence_df["prediction_source"] = evidence_df.apply(
        lambda row: normalize_text(row["prediction_source"]) or normalize_text(row["official_prediction_source_if_present"]),
        axis=1,
    )

    axes = evidence_df.apply(build_review_axes, axis=1)
    evidence_df["candidate_validity_review_axis"] = [axis[0] for axis in axes]
    evidence_df["date_judgement_review_axis"] = [axis[1] for axis in axes]
    evidence_df["evidence_summary_ko"] = evidence_df.apply(build_evidence_summary_ko, axis=1)
    evidence_df["review_question_ko"] = evidence_df.apply(build_review_question_ko, axis=1)
    evidence_df["recommended_sources_ko"] = evidence_df.apply(build_recommended_sources_ko, axis=1)

    evidence_df = evidence_df.loc[:, EVIDENCE_PACK_COLS].sort_values(
        ["round1_review_order", "site", "strict_trigger_date", "panel_id"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    packets_df = build_site_packets(evidence_df)
    prompts_df = evidence_df.loc[:, CASE_PROMPT_COLS].copy()
    return evidence_df, packets_df, prompts_df


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    evidence_df, packets_df, prompts_df = build_outputs(root, list(args.sites))

    out_dir = root / "_share"
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_df.to_csv(out_dir / "truth_review_evidence_pack_v1.csv", index=False, encoding="utf-8-sig")
    packets_df.to_csv(out_dir / "truth_review_site_packets_detailed_v1.csv", index=False, encoding="utf-8-sig")
    prompts_df.to_csv(out_dir / "truth_review_case_prompts_v1.csv", index=False, encoding="utf-8-sig")
    print(f"truth_review_evidence_pack_v1={len(evidence_df)}")


if __name__ == "__main__":
    main()
