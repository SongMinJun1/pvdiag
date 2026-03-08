#!/usr/bin/env bash
set -euo pipefail

SITE="${1:-kernelog1}"
SCORES="${2:-data/${SITE}/out/panel_day_risk_transition.csv}"
EVENTS="${3:-research/reports/${SITE}/fault_events_confirmed.csv}"
OUT="research/reports/${SITE}/paper_pack"

mkdir -p "${OUT}"

# 1) 컬럼 뷰 + 딕셔너리
python3 research/prognostics/make_paper_views.py --site "${SITE}"

# 2) ONEPAGER 재생성(예쁜 형식/NaN 처리)
python3 research/prognostics/make_onepager.py --site "${SITE}"

# 3) 케이스 플롯(확정고장 케이스 시각화)
if [ -f "${EVENTS}" ]; then
  python3 research/prognostics/plot_fault_cases.py \
    --scores "${SCORES}" \
    --events "${EVENTS}" \
    --out-dir "${OUT}/cases_v2" \
    --pre 120 --post 30
else
  echo "[WARN] events file not found: ${EVENTS} (skip case plots)"
fi

echo "[DONE] paper_pack ready -> ${OUT}"
