# Program Inventory

현재 소스 트리 기준으로 프로그램 파일을 active chain, support, review 대상으로 분류한 문서다.
이 문서는 "지금 당장 유지해야 하는 파일"과 "2차 검토가 필요한 파일"을 빠르게 구분하기 위한 인벤토리다.

## 1. core pipeline

| 파일 | 역할 | 현재 판단 |
|---|---|---|
| `pv_ae/pv_autoencoder_dayAE.py` | core engine, panel-day feature/diagnosis output 생성 | 최상위 SSOT |
| `research/prognostics/risk_score.py` | core output에 risk/cp score 추가 | 활성 체인 |
| `research/prognostics/add_transition_rankers.py` | transition rank 계층 추가 | 활성 체인 |
| `research/prognostics/add_ensemble_rankers.py` | ensemble rank 계층 추가 | 활성 체인 |
| `research/prognostics/run_scores_pipeline.py` | risk -> transition -> ensemble 오케스트레이션 | 활성 체인 |
| `research/prognostics/weaklabel_eval_2sigma.py` | weak-label 평가 onepage/CI 생성 | 활성 체인 |
| `research/prognostics/fault_case_study.py` | fault case markdown 요약 | 활성 체인 |
| `research/prognostics/plot_case_timeline.py` | 단일 패널 case timeline figure 생성 | 활성 체인 |
| `research/prognostics/ingest_gpvs_faults.py` | GPVS 원천 데이터 ingest 및 window score 생성 | GPVS 외부검증 core |
| `research/prognostics/external_eval_gpvs.py` | GPVS 외부검증 metric/onepage 생성 | GPVS 외부검증 core |

## 2. support tools

| 파일 | 역할 | 현재 판단 |
|---|---|---|
| `research/prognostics/run_dayae_site.py` | site 단위 엔진 실행 래퍼 | 지원 도구 |
| `research/prognostics/make_paper_views.py` | paper-friendly view/dictionary CSV 생성 | 지원 도구 |
| `research/prognostics/make_onepager.py` | 보고용 onepager 생성 | 지원 도구 |
| `research/prognostics/build_full_package.sh` | 결과 번들/패키지 생성 | 지원 도구 |
| `research/prognostics/run_paper_pack.sh` | paper pack 생성 진입점 | 지원 도구, `plot_fault_cases_v2.py` 호출 |
| `research/prognostics/README.md` | prognostics 사용 문서 | 지원 문서 |

## 3. review candidates

| 파일 | 역할 추정 | 연결 상태 |
|---|---|---|
| `research/prognostics/topk_workload2.py` | Top-K 평가 변형/후속 실험 | 현재 기준 활성 체인 직접 참조 흔적 없음 |
| `research/prognostics/eval_topk.py` | generic Top-K 평가 스크립트 | 현재 기준 활성 체인 직접 참조 흔적 없음 |
| `research/prognostics/eval_fault_topk_leadtime.py` | fault onset 기준 rank leadtime 평가 | 현재 기준 활성 체인 직접 참조 흔적 없음 |
| `research/prognostics/compare_rankers.py` | ranker 비교 실험 | `make_loss_labels.py` 산출(`highloss_q`) 의존 흔적 있음 |
| `research/prognostics/make_loss_labels.py` | future loss / highloss label 생성 | `compare_rankers.py`가 선행 실행 요구 |
| `research/prognostics/plot_fault_cases_v2.py` | fault case plot v2 생성 | `run_paper_pack.sh`에서 직접 호출 |

## 4. immediate keep list

아래 파일은 현재 체인의 SSOT 또는 외부검증 핵심이므로 우선 유지 대상으로 본다.

- `pv_ae/pv_autoencoder_dayAE.py`
- `research/prognostics/risk_score.py`
- `research/prognostics/add_transition_rankers.py`
- `research/prognostics/add_ensemble_rankers.py`
- `research/prognostics/run_scores_pipeline.py`
- `research/prognostics/weaklabel_eval_2sigma.py`
- `research/prognostics/fault_case_study.py`
- `research/prognostics/plot_case_timeline.py`
- `research/prognostics/ingest_gpvs_faults.py`
- `research/prognostics/external_eval_gpvs.py`

## 5. files requiring second-pass inspection

2차 검토 우선순위는 "활성 체인 직접 참조는 약하지만, 실험/보고 체인에서 혼선을 만들 수 있는 파일" 기준으로 잡는다.

| 파일 | 2차 검토 이유 |
|---|---|
| `research/prognostics/compare_rankers.py` | `make_loss_labels.py` 의존이 명시돼 있어 실험 체인 재현성 점검 필요 |
| `research/prognostics/make_loss_labels.py` | loss label 정의와 downstream 실험 연결이 맞는지 재검토 필요 |
| `research/prognostics/plot_fault_cases_v2.py` | `run_paper_pack.sh`에서 직접 호출되므로 실제 입력/출력 계약 확인 필요 |
| `research/prognostics/eval_fault_topk_leadtime.py` | 활성 체인 직접 참조는 없지만 평가 정의가 현재 문서 SSOT와 맞는지 확인 필요 |

## 6. archive

이번 1차 정리에서 archive로 이동한 파일들이다.

| 현재 위치 | 이전 위치 | 이동 사유 |
|---|---|---|
| `research/archive/prognostics/topk_workload.py` | `research/prognostics/topk_workload.py` | `topk_workload2.py` 대비 단순 버전, 활성 체인 직접 참조 없음 |
| `research/archive/prognostics/make_fault_case_plots.py` | `research/prognostics/make_fault_case_plots.py` | `plot_fault_cases_v2.py`와 기능 중복, active caller 없음 |
| `pv_ae/archive/scan_baseline.py` | `pv_ae/scan_baseline.py` | baseline 실험 보조 스크립트, 활성 체인 직접 참조 없음 |

## 연결 메모

- `research/prognostics/run_paper_pack.sh` -> `research/prognostics/plot_fault_cases_v2.py`
- `research/prognostics/compare_rankers.py` -> `research/prognostics/make_loss_labels.py`
- 위 두 연결 외 review candidates는 현재 기준 활성 체인에서 직접 참조 흔적을 찾지 못했다.
