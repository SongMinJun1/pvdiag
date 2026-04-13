# OPS_TRUTH_SEED_SAFE_PROMOTION_PACK_V1

## 목적
- 현재 preferred path인 `safe_same_label_only`를 실제 운영 가능한 sidecar/package로 구체화한다.
- safe 7건은 proposed canonical sidecar로 묶고
- gate 3건은 reviewer packet으로 따로 떼어낸다.

중요:
- 이 패치는 packaging/decision support 단계다.
- `panel_date_reaudit_working.csv`를 자동 overwrite하지 않는다.

## 왜 safe7이 full10보다 낮은 리스크인가
- safe7은 vendor truth에서 manual truth로 provenance만 바뀌고
  strict/lenient polarity가 그대로 유지된다.
- full10은 gate 3건 때문에 strict scoring universe 자체를 바꾼다.
- 즉 safe7은 baseline trust provenance를 강화하는 쪽이고,
  full10은 score/label semantics까지 건드릴 수 있다.

그래서 현재 운영 경로는:
- safe7은 sidecar로 먼저 promote 후보화
- gate3는 reviewer packet으로 hold

## 왜 gate3를 blind promote하면 안 되나
- conflict가 0이라는 것은 key-level 충돌이 없다는 뜻이다.
- 하지만 gate3는 strict label을 `exclude -> positive`로 바꾼다.
- 이건 semantic risk다.

즉 gate3는 reviewer evidence가 충분히 확인되기 전까지는
canonical truth로 올리면 안 된다.

## 산출물
- `_share/panel_date_reaudit_working_safe7_proposed_v1.csv`
- `_share/truth_seed_safe7_copyback_rows_v1.csv`
- `_share/truth_seed_gate3_review_packet_v1.csv`
- `_share/truth_seed_safe_promotion_summary_v1.csv`

## 파일 사용법

### `panel_date_reaudit_working_safe7_proposed_v1.csv`
- canonical 전체 row count를 유지한 sidecar proposal이다.
- safe 7건만 merge semantics로 반영되어 있다.
- 사람이 전체 diff를 검토한 뒤 수동 promote 판단을 내릴 때 사용한다.

### `truth_seed_safe7_copyback_rows_v1.csv`
- safe 7건만 따로 모은 promote 후보 목록이다.
- `apply_path = safe_same_label_promotion`으로 고정돼 있어 운영 메모나 reviewer 승인 리스트로 바로 쓸 수 있다.

### `truth_seed_gate3_review_packet_v1.csv`
- gate 3건만 담은 compact reviewer packet이다.
- `current_strict_truth_label`, `proposed_strict_truth_label`, `gate_reason`를 먼저 보고
- `evidence_summary_ko`, `review_question_ko`, `recommended_sources_ko`로 바로 재검토를 시작하면 된다.

### `truth_seed_safe_promotion_summary_v1.csv`
- current vs safe7 overall metric만 요약해서
  지금 safe7을 바로 promote할지,
  gate3까지 묶어서 hold할지를 결정한다.

## 요약 판단 규칙
- safe7 overall metric이 current 대비 전부 unchanged or improved면
  `promote_safe7_now_and_review_gate3`
- 하나라도 나빠지면
  `hold_all_until_gate_review`

## 운영 권장 순서
1. `truth_seed_safe_promotion_summary_v1.csv`에서 recommendation을 먼저 확인한다.
2. `truth_seed_safe7_copyback_rows_v1.csv`로 safe 7건 promote 후보를 검토한다.
3. `panel_date_reaudit_working_safe7_proposed_v1.csv`를 전체 canonical sidecar 관점에서 검토한다.
4. `truth_seed_gate3_review_packet_v1.csv`는 reviewer evidence 확인 전용으로 별도 처리한다.

## 핵심 원칙
- safe7 먼저
- gate3 hold
- canonical direct overwrite 금지
- reviewer sign-off 이후 수동 promote
