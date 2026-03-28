# OPS_TRUTH_REVIEW_COPYBACK_APPLY_V1

## 목적
- round-1 reviewer가 입력한 truth intake를 바로 canonical truth에 덮어쓰지 않고,
- 어떤 행이 안전하게 copyback 가능한지,
- 어떤 행이 충돌(conflict)인지,
- canonical sidecar proposal이 어떻게 보일지를 먼저 확인하기 위한 preview-only 단계다.

공식 prediction 출력은 바꾸지 않는다.  
`panel_date_reaudit_working.csv` 원본도 바꾸지 않는다.

## 왜 intake preview와 apply preview를 분리하나
- intake preview는 reviewer 입력 자체가 유효한지 본다.
- copyback apply preview는 그 유효 입력이 canonical 현재값과 충돌하지 않는지 본다.

즉:
- `truth_review_intake_preview_v1` = 입력 검수
- `truth_review_copyback_apply_v1` = canonical 반영 가능성 검수

이 둘을 분리해야 reviewer 입력 오류와 canonical 충돌을 섞지 않고 처리할 수 있다.

## 입력
- `_share/truth_review_intake_preview_v1.csv`
- `_share/panel_date_reaudit_working.csv`

## 출력
- `_share/truth_review_copyback_apply_summary_v1.csv`
- `_share/panel_date_reaudit_working_proposed_v1.csv`
- `_share/truth_review_copyback_rows_v1.csv`
- `_share/truth_review_copyback_conflicts_v1.csv`

## 적용 대상
아래 조건을 모두 만족하는 intake row만 apply preview 대상으로 본다.
- `intake_row_status == ready_for_copyback_preview`
- `copyback_ready_flag == 1`

그 외 행은 summary의 `untouched_or_nonready_count`로만 집계한다.

## 충돌 규칙
허용된 conflict 유형:
- `no_conflict`
- `candidate_validity_conflict`
- `date_judgement_conflict`
- `no_matching_canonical_row`

해석:
- `no_conflict`: canonical sidecar proposal에 안전하게 반영 가능
- `candidate_validity_conflict`: 현재 canonical 라벨과 reviewer 제안 라벨이 다름
- `date_judgement_conflict`: 현재 canonical 날짜 판단과 reviewer 제안이 다름
- `no_matching_canonical_row`: intake row가 canonical strict-case key와 매칭되지 않음

둘 다 충돌하면 `candidate_validity_conflict`를 우선 라벨로 쓰고, 세부 내용은 `conflict_detail`에 같이 남긴다.

## note 병합 규칙
`note`는 reviewer 메모를 버리지 않고 sidecar proposal에 안전하게 붙인다.

규칙:
- current blank + proposed nonblank -> proposed
- current nonblank + proposed blank -> current
- 둘 다 blank -> blank
- 둘 다 nonblank and identical -> current
- 둘 다 nonblank and different -> `current || review_v1: proposed`

즉 reviewer 메모는 원본 메모를 덮어쓰지 않고 provenance를 남긴다.

## 각 출력 파일 사용법

### `truth_review_copyback_rows_v1.csv`
- conflict가 없는 ready row만 들어간다.
- reviewer 입력이 canonical sidecar proposal에 어떻게 반영될지 row-level로 확인할 때 쓴다.
- 이 파일이 사실상 "manual promote 후보 목록"이다.

### `truth_review_copyback_conflicts_v1.csv`
- conflict가 있거나 canonical row를 찾지 못한 ready row가 들어간다.
- 바로 promote하지 말고 사람이 다시 본다.
- 특히 `candidate_validity_conflict`는 기존 canonical 판단과 reviewer 판단이 갈리는 케이스라 우선 확인해야 한다.

### `panel_date_reaudit_working_proposed_v1.csv`
- canonical 전체 row set을 유지한 sidecar proposal이다.
- row count는 현재 canonical과 같아야 한다.
- `no_conflict` row만 반영되어 있다.
- 원본 canonical 파일을 대신 쓰는 파일이 아니라, 사람이 검토 후 수동 promote할지 판단하는 preview 산출물이다.

## 언제 수동 promote가 안전한가
다음이 모두 맞아야 한다.
- `truth_review_copyback_rows_v1.csv` 기준으로 반영 대상이 명확하다.
- `truth_review_copyback_conflicts_v1.csv`에 남은 케이스가 수동 재검토되었다.
- `panel_date_reaudit_working_proposed_v1.csv` row count가 canonical과 동일하다.
- reviewer/owner가 어떤 rows를 올릴지 명시적으로 확인했다.

이 조건이 안 맞으면 canonical truth는 그대로 유지한다.

## 운영 권장 순서
1. reviewer가 `truth_review_copyback_rows_v1.csv`를 먼저 확인한다.
2. conflict가 있으면 `truth_review_copyback_conflicts_v1.csv`에서 원인별로 정리한다.
3. sidecar proposal인 `panel_date_reaudit_working_proposed_v1.csv`를 전체 diff 관점에서 검토한다.
4. 사람이 승인한 뒤에만 canonical truth에 수동 반영한다.

## 핵심 원칙
- direct overwrite 금지
- sidecar proposal 우선
- conflict 우선 해소
- manual provenance 유지
