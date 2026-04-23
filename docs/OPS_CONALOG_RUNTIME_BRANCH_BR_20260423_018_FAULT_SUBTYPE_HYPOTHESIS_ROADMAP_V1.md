<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_ROADMAP_V1

## [BR-20260423-018] Fault subtype hypothesis roadmap
- `status`: subtype_hypothesis_roadmap_locked
- `branch_type`: A
- `current_gate`: Gate 7
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-017은 고장 계열별 morphology atlas와 threshold 후보를 만들었다.
- 다음 단계에서는 계열 안에서 세부 고장 양상까지 나누어야 한다.
- 단, 세부 고장명은 운영 확정 라벨이 아니라 `hypothesis`로만 시작한다.
- 이유는 같은 계열 안에서도 전조 판단 기준이 다르기 때문이다.
  - 열화/오염/음영은 누적·반복 저하가 핵심이다.
  - 접속 불량/부분 개방은 지속성보다 재발성과 형태 유사성이 중요할 수 있다.
  - 다이오드/서브스트링은 전압/전류 비율과 낮 시간대 곡선 형태가 중요하다.
  - 센서/피드백/계측 이상은 실제 패널 고장이 아닐 수 있으므로 data QA 성격을 분리해야 한다.
  - 외부계통/공통 원인은 개별 패널 전조로 승격하면 위험하다.

## 2. Scope guard
- 이 branch는 roadmap/documentation only이다.
- `pv_ae/panel_day_engine.py`는 수정하지 않는다.
- production verdict, raw-only runtime semantics, current output은 수정하지 않는다.
- 세부 고장명은 `fault_subtype_hypothesis_shadow_ko` 후보이지 `최종고장양상_ko` 대체값이 아니다.
- 다음 구현도 operator-facing label 변경이 아니라 shadow column 추가부터 시작한다.

## 3. Locked schema for next shadow branch
다음 구현 branch는 아래 컬럼을 audit/shadow output에만 추가하는 방향으로 검토한다.

| column | meaning |
|---|---|
| `fault_family_hypothesis_shadow_ko` | BR-017 계열 가설 |
| `fault_subtype_hypothesis_shadow_ko` | 계열 안의 세부 고장 가설 |
| `subtype_evidence_tags` | duration/gap/continuity/severity/spatiality/VI-shape 등 근거 태그 |
| `subtype_confidence_shadow` | `low`, `medium`, `high`, `hold` 중 하나 |
| `subtype_hold_reason_ko` | 자동 승격하지 않는 이유 |
| `subtype_production_write_allowed` | 항상 `0`으로 시작 |

## 4. Subtype hypothesis map
- subtype rows: `17`
- evidence map:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv`

## 5. Initial subtype families
| family | subtype examples | first-pass action |
|---|---|---|
| `열화·오염·음영 계열` | 누적 오염·열화형, 국소 음영 패턴형, 일시 환경 episode형, 장기 gap 단일 저하 보류형 | 반복/누적 증거 없으면 전조 승격 금지 |
| `접속 불량·부분 개방 계열` | 간헐 접촉저항형, 부분 개방 진행형, 커넥터·단자·퓨즈 계열 의심형 | 재발성·형태 유사성 중심으로 manual review candidate |
| `다이오드·서브스트링 계열` | bypass diode 동작·고장 의심형, 서브스트링 전류 제한형, 국소 셀 손상 proxy형 | VI ratio와 낮 시간대 곡선형을 shadow evidence로 요구 |
| `센서·피드백·계측 이상 계열` | 센서 scale drift형, dropout·freeze형, timestamp·채널 매칭 이상형 | 패널 고장으로 직접 승격하지 않고 hold_episode_only |
| `외부계통·공통원인 계열` | site-wide grid/inverter 교란형, root·MPPT group 공통 episode형, 날씨·일사 공통 episode형 | 개별 패널 전조 승격 차단 |
| `strict trigger anchored sudden fault` | strict 근접 급작형 | 반복 전조 없으면 no_precursor_promotion |

## 6. Decision locks
- subtype은 production 판정이 아니라 evidence-rich hypothesis이다.
- family가 같아도 subtype마다 전조 조건을 다르게 둔다.
- 세부 고장 hypothesis는 최소 2개 이상의 축으로 방어되어야 한다.
  - 예: duration + continuity
  - 예: recurrence + VI shape
  - 예: spatiality + fast recovery
- 한 축만 맞는 경우는 `manual_review_candidate` 또는 `hold_episode_only`로 둔다.
- 센서/계측 subtype은 패널 고장 subtype과 분리한다.
- external/common-cause subtype은 개별 패널 전조 승격 전에 group/site episode로 분리한다.

## 7. Reproduction
- before command:
  - `git status -sb`
- documentation validation command:
```bash
python - <<'PY'
import csv
from pathlib import Path

p = Path("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv")
rows = list(csv.DictReader(p.open(newline="")))
assert len(rows) == 17
assert {r["recommended_shadow_action"] for r in rows} <= {
    "shadow_subtype_candidate",
    "manual_review_candidate",
    "hold_episode_only",
    "block_precursor_backdating",
    "block_individual_precursor",
    "no_precursor_promotion",
}
assert all(r["subtype_key"] and r["primary_signature_ko"] for r in rows)
print("BR-018 subtype roadmap OK")
PY
```
- code safety command:
  - `python -m py_compile pv_ae/panel_day_engine.py`

## 8. Next safe implementation
- BR-019 candidate:
  - add subtype hypothesis shadow columns to the audit/evidence layer only.
  - reuse BR-017 episode features and BR-018 subtype map.
  - keep `subtype_production_write_allowed = 0`.
  - rerun fresh tri-site evidence before considering any operator-facing label change.
