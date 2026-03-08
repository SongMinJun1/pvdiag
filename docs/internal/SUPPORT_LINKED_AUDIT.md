# Support Linked Audit

이 문서는 아직 `research/prognostics/`에 남아 있는 support 그룹 3개 파일의 연결 관계와 이동 가능성을 다시 감사한 기록이다.
목적은 직접 caller, 상대 경로 의존, support 간 결합을 확인해서 다음 이동 작업의 위험도를 문서로 고정하는 것이다.

## Summary Table

| 파일명 | 현재 역할 한 줄 요약 | 직접 호출하는 파일 | 호출되는 위치 | 입력 파일 | 출력 파일 | 상대 경로 의존 여부 | 다른 support 파일과의 결합 여부 | 이동 가능성 판정 | 추천 새 위치 | 추천 새 이름 | 판정 이유 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `research/support/prognostics/compare_rankers.py` | future loss 라벨 위에서 ranking 컬럼별 capture/precision/lift를 비교하는 실험 비교기 | 없음 | 코드 기준 자동 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:51`, `docs/internal/PROGRAM_INVENTORY.md:39`, `docs/internal/PROGRAM_REVIEW.md:44`, `research/support/prognostics/compare_rankers.py:127` | `--in` loss label 포함 score CSV, `--cols` ranker 목록 | `--out` CSV | 없음. 입출력 모두 CLI 인자 기반 | 예. `make_loss_labels.py`가 생성하는 `future_loss_Hd`, `highloss_q` 컬럼에 결합 | `moved to support` | `research/support/prognostics/` | `compare_rankers.py` | linked support pair로 실제 이동 완료. runtime caller는 없고, 실험 체인에서만 결합된다. |
| `research/support/prognostics/make_loss_labels.py` | panel-day risk CSV에 future loss 및 `highloss_q` 라벨을 추가하는 전처리기 | 없음 | 코드 기준 자동 caller 없음. 참조는 `docs/RELEASE_MANIFEST.md:52`, `docs/internal/PROGRAM_INVENTORY.md:40`, `docs/internal/PROGRAM_REVIEW.md:53`, `research/support/prognostics/compare_rankers.py:127` | `--in` panel-day risk 계열 CSV | `--out` CSV (`daily_loss`, `future_loss_{H}d`, `highloss_q` 추가) | 없음. 입출력 모두 CLI 인자 기반 | 예. downstream `compare_rankers.py`가 생성 컬럼에 결합 | `moved to support` | `research/support/prognostics/` | `make_loss_labels.py` | linked support pair로 실제 이동 완료. support 실험 체인에서 선행 단계 역할은 유지된다. |
| `research/prognostics/plot_fault_cases.py` | paper pack용 fault case CSV/PNG를 생성하는 현재형 case plotter | 없음 | 직접 caller: `research/prognostics/run_paper_pack.sh:19`; 간접 caller: `research/prognostics/build_full_package.sh:10`, `research/prognostics/build_full_package.sh:85` | `--scores` CSV, `--events` fault event CSV | `case_<panel>.csv`, `case_<panel>.png` in `--out-dir` | 있음. `run_paper_pack.sh`가 현재 경로를 하드코딩 | 약함. 다른 support Python과 직접 결합은 없지만 shell caller 체인에 묶임 | `keep in place for now` | 추후 `research/support/prognostics/` 검토 | `plot_fault_cases.py` 유지 | 현재 위치가 shell caller에 박혀 있다. 지금 옮기면 `run_paper_pack.sh`와 `build_full_package.sh`가 깨지므로 우선 제자리에 두는 것이 맞다. |

## Link Table: `compare_rankers.py` <-> `make_loss_labels.py`

| upstream | downstream | 연결 방식 | 코드 근거 | 현재 결론 |
|---|---|---|---|---|
| `research/support/prognostics/compare_rankers.py` | `research/support/prognostics/make_loss_labels.py` | subprocess 호출은 없고, 생성 컬럼 계약에 의존 | `research/support/prognostics/compare_rankers.py:127`의 `Re-run make_loss_labels.py first.` 문구와 `future_loss_Hd`, `highloss_q` 요구 | 둘은 함께 support 위치로 이동 완료 |

해석:
- 코드 import는 없지만, 실험 체인 의미상 `make_loss_labels.py`가 upstream이다.
- 한쪽만 이동하면 실행 예시와 문서가 분리될 가능성이 높다.
- 따라서 둘은 `move with path fixes`가 적절하다.

## Link Table: `run_paper_pack.sh` -> `plot_fault_cases.py`

| caller | callee | 호출 방식 | 추가 caller | 현재 결론 |
|---|---|---|---|---|
| `research/prognostics/run_paper_pack.sh` | `research/prognostics/plot_fault_cases.py` | `python3 research/prognostics/plot_fault_cases.py ...` | `research/prognostics/build_full_package.sh`가 `run_paper_pack.sh` 호출 | 지금은 `plot_fault_cases.py`를 그대로 두는 것이 맞다 |

해석:
- `plot_fault_cases.py`는 Python 내부 결합보다 shell 경로 결합이 더 강하다.
- 이동 자체는 어렵지 않지만, caller 두 개를 같이 고쳐야 하므로 "지금 즉시 이동" 대상은 아니다.
- 이 파일은 archive 후보가 아니라 현재 paper-pack 체인 유지 파일이다.

## Final Recommendation

### keep in place for now
- `research/prognostics/plot_fault_cases.py`

### moved to support
- `research/support/prognostics/compare_rankers.py`
- `research/support/prognostics/make_loss_labels.py`

### archive candidate
- 없음

## Why No Archive Candidate Yet

- `research/support/prognostics/compare_rankers.py`와 `research/support/prognostics/make_loss_labels.py`는 여전히 실험 체인에서 한 쌍의 평가 도구로 의미가 있다.
- `plot_fault_cases.py`는 `run_paper_pack.sh`에 직접 연결된 현재형 support 파일이다.
- 따라서 이번 감사 기준으로는 세 파일 모두 archive보다는 유지 또는 경로 수정 후 이동이 타당하다.
