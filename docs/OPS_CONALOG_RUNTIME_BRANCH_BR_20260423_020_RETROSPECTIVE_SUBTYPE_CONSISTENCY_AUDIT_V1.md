<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_020_RETROSPECTIVE_SUBTYPE_CONSISTENCY_AUDIT_V1

## [BR-20260423-020] Retrospective subtype consistency audit
- `status`: retrospective_subtype_consistency_audit_complete
- `branch_type`: A
- `current_gate`: Gate 7
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-017~019에서 목표 해상도가 올라갔다.
- 이전 목표는 `전조형 고장`과 `급작 고장`의 event semantics를 안전하게 정리하는 것이었다.
- 새 목표는 한 단계 더 들어가서, 전조/고장 신호가 어떤 세부 고장 subtype으로 이어질 가능성이 있는지 shadow evidence로 추적하는 것이다.
- 이 목표가 추가되었으므로 과거 BR 결정을 다시 뒤집을 필요가 있는지 확인했다.

## 2. Scope guard
- 코드와 production verdict는 수정하지 않는다.
- 과거 branch를 되돌리거나 rewrite하지 않는다.
- 이번 산출물은 retrospective audit only이다.
- 판단 단위는 개별 commit이 아니라 decision group이다.
- 핵심 질문은 "semantic reopen이 필요한가"와 "shadow follow-up이 필요한가"이다.

## 3. Headline result
- semantic reopen required: `0`
- operator-facing rollback required: `0`
- production verdict patch required: `0`
- shadow follow-up required groups: `3`
- conclusion:
  - 과거 결정은 뒤집지 않는다.
  - subtype 목표는 과거 결정을 반박하는 새 원칙이 아니라, 과거 결정을 더 높은 해상도로 설명하는 새 lens다.

## 4. Review summary
| review_group | branches | status | semantic_reopen | shadow_followup |
|---|---|---|---:|---:|
| `G1_backdating_guard_chain` | `BR-002, BR-012, BR-013, BR-014, BR-015, BR-016` | `keep` | 0 | 0 |
| `secondary_window_promotion_chain` | `BR-004, BR-005, BR-006, BR-010, BR-011` | `keep_with_shadow_followup` | 0 | 1 |
| `ktc_strict_common_hold` | `BR-007` | `keep` | 0 | 0 |
| `promotion_decision_contract` | `BR-008, BR-009` | `keep_with_schema_extension` | 0 | 1 |
| `fault_family_atlas` | `BR-017` | `keep` | 0 | 0 |
| `subtype_roadmap` | `BR-018` | `keep` | 0 | 0 |
| `subtype_shadow_implementation` | `BR-019` | `keep_with_shadow_followup` | 0 | 1 |

## 5. Key reasoning
- G1 chain:
  - BR-016 applying 6 strict-proximal G1 rows still holds.
  - BR-019 makes the explanation cleaner: these are `장기 gap 단일 저하 보류형`, not confirmed precursor subtype rows.
- Secondary-window chain:
  - no promotion remains correct.
  - however, blocked/manual-review cases should be revisited with subtype shape tags so a real recurring contact/open pattern is not hidden by promotion blocker logic.
- Promotion-decision contract:
  - still valid as an audit decision layer.
  - future schema should not overload one confidence value with both "shape looks plausible" and "promotion is blocked".
- BR-017/018/019:
  - these are the current subtype path and should remain the foundation.
  - BR-019 intentionally keeps every subtype as `hold`; that is conservative but needs better decomposition next.

## 6. Next safe implementation
- Add separate shadow columns:
  - `subtype_shape_confidence_shadow`
  - `subtype_promotion_blocker_shadow`
  - `subtype_promotion_blocker_reason_ko`
- Keep:
  - `subtype_production_write_allowed = 0`
  - no operator-facing label change
  - no final verdict change
- Then rerun fresh tri-site and check whether any cases can safely move from `hold` to shape-level `low/medium` without promotion.

## 7. Evidence outputs
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_020_RETROSPECTIVE_SUBTYPE_CONSISTENCY_AUDIT_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_020_RETROSPECTIVE_SUBTYPE_CONSISTENCY_VALIDATION_V1.json`

## 8. Reproduction
- before command:
  - `git status -sb`
- audit validation command:
```bash
python - <<'PY'
import csv
import json
from pathlib import Path

audit = Path("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_020_RETROSPECTIVE_SUBTYPE_CONSISTENCY_AUDIT_V1.csv")
rows = list(csv.DictReader(audit.open(newline="")))
assert len(rows) == 7
assert sum(int(r["semantic_reopen_required"]) for r in rows) == 0
assert sum(int(r["shadow_followup_required"]) for r in rows) == 3
assert {r["consistency_status"] for r in rows} <= {
    "keep",
    "keep_with_shadow_followup",
    "keep_with_schema_extension",
}
validation = json.loads(Path("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_020_RETROSPECTIVE_SUBTYPE_CONSISTENCY_VALIDATION_V1.json").read_text())
assert validation["semantic_reopen_required_sum"] == 0
assert validation["shadow_followup_required_sum"] == 3
print("BR-020 retrospective subtype consistency audit OK")
PY
```
- code safety command:
  - `python -m py_compile pv_ae/panel_day_engine.py`

## 9. Decision
- Do not reopen or revert prior runtime semantics.
- Continue forward with subtype decomposition as a shadow-only evidence refinement.
- The next branch should split subtype shape confidence from promotion blocker.
