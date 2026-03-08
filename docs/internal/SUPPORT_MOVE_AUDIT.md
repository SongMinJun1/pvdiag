# Support Move Audit

이 문서는 support 성격 스크립트를 이동하기 전에, 현재 코드 트리 기준으로 runtime caller, 상대 경로 의존, sibling 의존을 점검한 안전 감사 문서다.
목표는 "지금 바로 옮겨도 되는지", "경로 수정이 필요한지", "당장은 유지해야 하는지"를 코드 수정 없이 구분하는 것이다.

## Summary Table

| 파일명 | 현재 역할 한 줄 요약 | 직접 호출하는 파일 | 호출되는 경로 / 참조 위치 | 상대 경로 의존 여부 | 로컬 import / sibling 의존 여부 | 이동 가능성 판정 | 추천 새 위치 | 추천 새 이름 | 판정 이유 |
|---|---|---|---|---|---|---|---|---|---|
| `research/prognostics/topk_workload2.py` | Top-K 선정 패널의 반복 선택 빈도를 집계하는 workload/집중도 보조 평가기 | 없음 | 코드 기준 직접 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:48`, `docs/internal/PROGRAM_INVENTORY.md:36`, `docs/internal/PROGRAM_REVIEW.md:17` | 없음. 입력/출력 모두 CLI 인자 기반 | 없음 | `safe to move now` | `research/support/prognostics/` | `topk_workload2.py` | 하드코딩 caller, sibling import, 상대 경로 의존이 없다. 이동 시 깨지는 것은 문서/사용자 호출 습관뿐이라 코드 관점에서는 바로 이동 가능하다. |
| `research/prognostics/eval_topk.py` | future loss 라벨 기준 Top-K capture/precision 평가기 | 없음 | 코드 기준 직접 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:49`, `docs/internal/PROGRAM_REVIEW.md:26` | 없음. `--in`, `--out-dir`, `--events` 모두 외부 인자 | 없음 | `safe to move now` | `research/support/prognostics/` | `eval_topk.py` | generic evaluator이며 현재 자동 호출 체인에 묶여 있지 않다. 입력/출력이 전부 인자 기반이라 경로 이동 리스크가 낮다. |
| `research/prognostics/eval_fault_topk_leadtime.py` | onset_date 기준 최초 Top-K 진입일과 leadtime을 계산하는 fault-based 평가기 | 없음 | 코드 기준 직접 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:50`, `docs/internal/PROGRAM_REVIEW.md:35`, 파일 자체 docstring | 없음. `--scores`, `--events`, `--out` 모두 외부 인자 | 없음 | `safe to move now` | `research/support/prognostics/` | `eval_fault_topk_leadtime.py` | `eval_topk.py`와 역할은 다르지만 runtime caller가 없다. CLI 경로만 맞추면 되므로 지금 이동해도 코드 체인에는 영향이 없다. |
| `research/prognostics/compare_rankers.py` | 동일 loss 라벨에서 ranking 컬럼 성능을 비교하는 ranker 비교기 | 없음 | 코드 기준 자동 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:51`, `docs/internal/PROGRAM_REVIEW.md:44`, `research/prognostics/compare_rankers.py:127` | 없음. 입출력은 CLI 인자 기반 | 직접 import는 없지만 `make_loss_labels.py`가 만드는 `future_loss_Hd`, `highloss_q` 컬럼에 의존 | `move with path fixes` | `research/support/prognostics/` | `compare_rankers.py` | 코드상 하드 caller는 없지만 실험 체인에서 `make_loss_labels.py`와 짝으로 쓰인다. 이동 자체는 가능하나 문서/실행 예시/사용자 호출 경로를 같이 고치는 편이 안전하다. |
| `research/prognostics/make_loss_labels.py` | `future_loss_Hd`와 `highloss_q`를 생성하는 loss-label 전처리기 | 없음 | 코드 기준 자동 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:52`, `docs/internal/PROGRAM_REVIEW.md:53`, `research/prognostics/compare_rankers.py:127` | 없음. 입출력은 CLI 인자 기반 | 직접 import는 없지만 downstream가 생성 컬럼에 의존 | `move with path fixes` | `research/support/prognostics/` | `make_loss_labels.py` | standalone 스크립트지만 `compare_rankers.py`가 사실상 선행 실행을 가정한다. 따라서 쌍으로 이동하고 안내 경로를 같이 정리하는 것이 안전하다. |
| `research/prognostics/plot_fault_cases_v2.py` | paper pack용 fault case 시계열/그림 생성기 | 없음 | 직접 caller: `research/prognostics/run_paper_pack.sh:19`; 간접 caller: `research/prognostics/build_full_package.sh:10`, `research/prognostics/build_full_package.sh:85`를 통해 `run_paper_pack.sh` 호출 | 있음. `run_paper_pack.sh`가 현재 파일 경로를 하드코딩 | 없음 | `keep in place for now` | 추후 `research/support/prognostics/` 검토 | `plot_fault_cases_v2.py` 유지 | runtime shell caller가 하드코딩되어 있어 지금 이동하면 `run_paper_pack.sh`와 `build_full_package.sh`가 즉시 깨진다. 먼저 caller 경로 수정이 선행돼야 한다. |

## Special Link: `run_paper_pack.sh` -> `plot_fault_cases_v2.py`

| caller | callee | 호출 방식 | 경로 고정 여부 | 현재 결론 |
|---|---|---|---|---|
| `research/prognostics/run_paper_pack.sh` | `research/prognostics/plot_fault_cases_v2.py` | `python3 research/prognostics/plot_fault_cases_v2.py ...` | 예. 상대 경로가 shell 안에 하드코딩 | 지금은 `plot_fault_cases_v2.py`를 유지해야 한다 |

추가 메모:
- `research/prognostics/build_full_package.sh:10`, `research/prognostics/build_full_package.sh:85`가 `run_paper_pack.sh`를 호출하므로, 실제로는 2단 caller 체인이다.
- 따라서 `plot_fault_cases_v2.py` 이동은 단일 파일 이동이 아니라 shell caller 정리 작업이다.

## Special Link: `compare_rankers.py` -> `make_loss_labels.py`

| upstream | downstream dependency | 코드 근거 | 현재 결론 |
|---|---|---|---|
| `research/prognostics/compare_rankers.py` | `research/prognostics/make_loss_labels.py` | `research/prognostics/compare_rankers.py:127`의 `Re-run make_loss_labels.py first.` 문구와 `future_loss_Hd`, `highloss_q` 컬럼 요구 | 두 파일은 같은 support 위치로 함께 옮기는 것이 안전하다 |

추가 메모:
- subprocess 호출은 없지만, 실험 체인에서는 `make_loss_labels.py`가 선행 단계다.
- 한쪽만 옮기면 실행 예시와 사용자 습관이 분리될 가능성이 높다.

## Relationship: `topk_workload2.py`, `eval_topk.py`, `eval_fault_topk_leadtime.py`

| 파일 | 평가 대상 | 입력 전제 | 다른 두 파일과의 관계 |
|---|---|---|---|
| `topk_workload2.py` | Top-K에 반복적으로 등장하는 패널 분포 | 날짜/패널/랭커 컬럼이 있는 score CSV | 순위 집중도 보조 평가기이며 `eval_*`와 보완 관계 |
| `eval_topk.py` | future loss 기준 capture/precision | `future_loss_Hd`, 선택적으로 `highloss_q` | loss-based evaluator |
| `eval_fault_topk_leadtime.py` | onset 이전 최초 Top-K 진입 leadtime | `fault_events_auto.csv`, score CSV | fault-based evaluator |

해석:
- 세 파일은 서로 import/호출 관계가 없다.
- 같은 점수 CSV를 평가하지만, 목적이 다르다: `topk_workload2.py`는 집중도, `eval_topk.py`는 loss label, `eval_fault_topk_leadtime.py`는 onset leadtime을 본다.
- 따라서 파일 병합 대상은 아니고, 위치만 함께 `support`로 묶는 것이 적절하다.

## Move Recommendation

### 바로 옮겨도 되는 파일
- `research/prognostics/topk_workload2.py`
- `research/prognostics/eval_topk.py`
- `research/prognostics/eval_fault_topk_leadtime.py`

### 경로 수정과 함께 옮겨야 하는 파일
- `research/prognostics/compare_rankers.py`
- `research/prognostics/make_loss_labels.py`

### 지금은 그대로 두는 게 맞는 파일
- `research/prognostics/plot_fault_cases_v2.py`

## Recommended Destination Policy

- support 유지 대상의 기본 목적지는 `research/support/prognostics/`
- 직접 runtime caller가 없는 standalone evaluator는 먼저 `research/support/prognostics/`로 이동 가능
- shell caller가 경로를 하드코딩한 파일은 caller 정리 이후 이동
