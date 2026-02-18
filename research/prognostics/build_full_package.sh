#!/usr/bin/env bash
set -euo pipefail

SITE="${1:-kernelog1}"
DATE="$(date +%Y%m%d)"
BUNDLE="release_bundle_${SITE}_${DATE}"
ZIP="${BUNDLE}.zip"

# 0) 최신 paper_pack 생성(표/그림/ONEPAGER)
bash research/prognostics/run_paper_pack.sh "${SITE}"

PACK="research/reports/${SITE}/paper_pack"

# 1) 초기화
rm -rf "${BUNDLE}" "${ZIP}"
mkdir -p "${BUNDLE}"/{docs,results,code,meta}

# 2) 문서/결과 복사(공유 핵심)
cp "${PACK}/ONEPAGER.md" "${BUNDLE}/docs/01_ONEPAGER.md"
cp "${PACK}/data_dictionary_paper.md" "${BUNDLE}/docs/02_data_dictionary_paper.md" 2>/dev/null || true
cp "${PACK}/flowchart.mmd" "${BUNDLE}/docs/03_flowchart.mmd" 2>/dev/null || true
cp "${PACK}/flowchart.png" "${BUNDLE}/docs/03_flowchart.png" 2>/dev/null || true

mkdir -p "${BUNDLE}/results/cases_v2" "${BUNDLE}/results/tables"
cp "${PACK}/cases_v2/"*.png "${BUNDLE}/results/cases_v2/" 2>/dev/null || true
cp "${PACK}/table_events.csv" "${BUNDLE}/results/tables/" 2>/dev/null || true
cp "${PACK}/table_leadtime_k20.csv" "${BUNDLE}/results/tables/" 2>/dev/null || true
cp "${PACK}/table_workload_metrics.csv" "${BUNDLE}/results/tables/" 2>/dev/null || true
cp "${PACK}/scores_view_core.csv" "${BUNDLE}/results/" 2>/dev/null || true

# 3) 코드 복사(정크 제외)
#    - raw/out, reports 대용량, venv/cache 류는 제외
EXCLUDES=(
  "--exclude=.git/"
  "--exclude=.DS_Store"
  "--exclude=__pycache__/"
  "--exclude=*.pyc"
  "--exclude=.pytest_cache/"
  "--exclude=.ipynb_checkpoints/"
  "--exclude=.venv/"
  "--exclude=venv/"
  "--exclude=node_modules/"
  "--exclude=dist/"
  "--exclude=build/"
  "--exclude=${BUNDLE}/"
  "--exclude=research/reports/"
  "--exclude=data/*/raw/"
  "--exclude=data/*/out/"
)

rsync -a "${EXCLUDES[@]}" ./ "${BUNDLE}/code/"

# 4) 메타/점검 리포트 생성
python3 -V > "${BUNDLE}/meta/python_version.txt" 2>&1 || true
python3 -m pip freeze > "${BUNDLE}/meta/pip_freeze.txt" 2>/dev/null || true

# 가장 큰 파일(정크 확인용)
( cd "${BUNDLE}" && find . -type f -print0 | xargs -0 du -k | sort -nr | head -80 ) \
  > "${BUNDLE}/meta/TOP80_LARGEST_FILES_KB.txt" || true

# 정크 후보 목록(패턴 매칭)
( cd "${BUNDLE}" && find . -type f | egrep -i "(data/.*/raw|data/.*/out|__pycache__|\.venv|node_modules|\.ipynb_checkpoints|\.DS_Store)" ) \
  > "${BUNDLE}/meta/JUNK_CANDIDATES.txt" || true

# 비밀키/토큰 의심 문자열 스캔(없어야 정상)
( cd "${BUNDLE}/code" && grep -RIn --exclude-dir .git -E "(api[_-]?key|secret|token|password|sk-[A-Za-z0-9]{20,})" . ) \
  > "${BUNDLE}/meta/SECRET_SCAN.txt" 2>/dev/null || true

# 번들 파일 리스트
( cd "${BUNDLE}" && find . -type f | sort ) > "${BUNDLE}/meta/FILELIST.txt"

# README
cat > "${BUNDLE}/README.md" <<EOF
# Full package (${SITE})

## 읽는 순서(추천)
1) docs/01_ONEPAGER.md
2) docs/03_flowchart.(png|mmd)
3) results/cases_v2/ (케이스 타임라인)
4) results/tables/ (events/leadtime/workload)
5) code/ (원본 알고리즘 코드)

## 재현 실행
- 프로젝트 루트에서:
  bash research/prognostics/run_paper_pack.sh ${SITE}

## 점검 리포트
- meta/TOP80_LARGEST_FILES_KB.txt : 대용량/정크 확인
- meta/SECRET_SCAN.txt : 토큰/키 의심 문자열(비어있어야 정상)
EOF

# 5) ZIP 생성
zip -r "${ZIP}" "${BUNDLE}" >/dev/null
echo "[OK] bundle zip: ${ZIP}"
echo "[CHECK] open meta/TOP80_LARGEST_FILES_KB.txt and meta/SECRET_SCAN.txt before upload"
