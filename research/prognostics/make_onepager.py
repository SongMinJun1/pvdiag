import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def _read(p: Path):
    if not p.exists():
        return None
    return pd.read_csv(p, encoding="utf-8-sig")

def _fmt(x):
    if pd.isna(x):
        return "—"
    # 숫자는 보기 좋게
    if isinstance(x, (float, np.floating)):
        if np.isfinite(x) and abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f"{float(x):.4g}"
    return str(x)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="kernelog1")
    ap.add_argument("--pack", default=None, help="paper_pack dir (optional)")
    args = ap.parse_args()

    pack = Path(args.pack) if args.pack else Path(f"research/reports/{args.site}/paper_pack")
    pack.mkdir(parents=True, exist_ok=True)

    events = _read(pack / "table_events.csv")
    lead = _read(pack / "table_leadtime_k20.csv")
    work = _read(pack / "table_workload_metrics.csv")

    lines = []
    lines.append(f"# PV Fault Early-Warning & Diagnosis — ONEPAGER ({args.site})\n")
    lines.append("## 한 줄 정의")
    lines.append("- 본 시스템은 5분 V/I로부터 DC power를 만들고, peer(동료 패널 중앙값) 대비 ratio로 정규화한 뒤,")
    lines.append("  (1) 상태(Severity), (2) 형태(Shape: AE/DTW), (3) 난류(Turbulence: HS), (4) 전이(Transition) 신호를 생성하여")
    lines.append("  **전조(Top‑K 우선순위)** 와 **확정진단(final_fault)** 을 분리 산출한다.\n")

    lines.append("## 출력(Two-head)")
    lines.append("- **전조/예측 헤드**: transition_rank(변화), AE rank(모양) 등으로 *점검 우선순위 Top‑K*를 만든다.")
    lines.append("- **진단/확정 헤드**: state_dead → dead_streak → final_fault 로 보수적으로 확정고장을 판정한다.\n")

    lines.append("## 핵심 컬럼(설명용 Core)")
    lines.append("| canonical | 의미 |")
    lines.append("|---|---|")
    core = [
        ("midday_ratio", "정오 출력비(패널/peer)"),
        ("level_drop", "상태 저하량(1-midday_ratio)"),
        ("coverage_midday", "정오 데이터 품질"),
        ("peer_midday_frac", "사이트가 살아있었는지(정오 peer 발전 수준)"),
        ("ae_rank", "모양 이상(날짜 내 순위/분위)"),
        ("transition_rank", "최근 변화(전이) 이상(날짜 내 순위/분위)"),
        ("transition_cp_rank", "전이 + change-point 보강 순위"),
        ("dead_streak", "dead 연속일수"),
        ("final_fault", "확정고장 플래그"),
    ]
    for c, d in core:
        lines.append(f"| `{c}` | {d} |")
    lines.append("")

    lines.append("## 결과 요약(현재 확보 데이터 기준)")
    if events is not None and len(events):
        lines.append("\n### 사건 정의(onset vs diagnosis)")
        lines.append("| panel_id | onset_date | diagnosis_date | delay_days |")
        lines.append("|---|---:|---:|---:|")
        for _, r in events.iterrows():
            lines.append(f"| {_fmt(r.get('panel_id'))} | {_fmt(r.get('onset_date'))} | {_fmt(r.get('diagnosis_date'))} | {_fmt(r.get('diagnosis_delay_days'))} |")
    else:
        lines.append("- (table_events.csv 없음)")

    if lead is not None and len(lead):
        lines.append("\n### 전조 리드타임(Top‑K=20, onset 기준)")
        lines.append("> 값 = onset보다 **몇 일 먼저** Top‑K에 진입했는지 (빈칸=진입 못함)")
        lines.append("| panel_id | onset | ae_rank | level_drop | risk_day | transition_cp | transition |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for _, r in lead.iterrows():
            lines.append(
                f"| {_fmt(r.get('panel_id'))} | {_fmt(r.get('onset_date'))} | "
                f"{_fmt(r.get('ae_rank'))} | {_fmt(r.get('level_drop'))} | {_fmt(r.get('risk_day'))} | "
                f"{_fmt(r.get('transition_cp_rank_day'))} | {_fmt(r.get('transition_rank_day'))} |"
            )
    else:
        lines.append("- (table_leadtime_k20.csv 없음)")

    if work is not None and len(work):
        lines.append("\n### Workload/회전성(오경보 부담 대체 지표)")
        lines.append("- max_share_days: 1개 패널이 Top‑K를 점령한 최대 비율(높을수록 고착)")
        lines.append("- effective_panels: 회전/다양성(높을수록 좋음)")
        lines.append("| ranker | max_share_days | effective_panels | top20_pick_share |")
        lines.append("|---|---:|---:|---:|")
        for _, r in work.iterrows():
            lines.append(f"| {_fmt(r.get('ranker'))} | {_fmt(r.get('max_share_days'))} | {_fmt(r.get('effective_panels'))} | {_fmt(r.get('top20_pick_share'))} |")
    else:
        lines.append("- (table_workload_metrics.csv 없음)")

    lines.append("\n## 60초 설명 스크립트(그대로 읽기)")
    lines.append("1) 5분 V/I로 P를 만들고, 같은 시각 peer 중앙값으로 나눠 ratio로 정규화한다(날씨 영향 감소).")
    lines.append("2) 정오(midday) 구간 ratio 평균으로 상태(Severity)를 만들고, coverage로 품질을 게이트한다.")
    lines.append("3) 하루 ratio 곡선(96포인트)에서 AE/DTW/HS로 형태/난류 이상을 점수화한다.")
    lines.append("4) 패널 자기 과거 대비 변화(transition)로 ‘최근에 새로 나빠짐’을 전조로 잡아 Top‑K 우선순위를 만든다.")
    lines.append("5) 확정고장은 state_dead가 dead_streak로 누적될 때만 보수적으로 final_fault로 확정한다.")

    out = pack / "ONEPAGER.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("[OK] wrote", out)

if __name__ == "__main__":
    main()
