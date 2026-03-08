# Program Review

현재 브랜치 `classify-program-files` 기준으로 review 대상 프로그램 파일을 2차 검토한 문서다.
목적은 "활성 체인에 직접 묶여 있는지", "실험 보조인지", "보관 후보인지"를 코드 수정 없이 판정하는 것이다.

## Review Table

### 1) `research/archive/prognostics/topk_workload.py`
- 현재 역할 한 줄 요약: 단일 ranker 기준 날짜별 Top-K 패널 빈도를 집계하는 가장 단순한 workload 스크립트.
- 실제 입력 파일: `--scores`로 주는 panel-day score CSV, `--ranker` 컬럼.
- 실제 출력 파일: `--out` CSV (`panel_id`, `days_in_topk`, `share_days`).
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음.
- 현재 체인에서의 필요도: `archived`
- 판정 이유: 기능이 매우 단순하고 `topk_workload2.py`가 exclusion 옵션까지 포함한 상위 호환에 가깝다. 현재 활성 체인에서 직접 참조도 없어 1차 정리에서 archive로 이동했다.
- 즉시 삭제하면 안 되는 파일: `아니오`

### 2) `research/support/prognostics/topk_workload2.py`
- 현재 역할 한 줄 요약: `topk_workload.py`의 확장판으로 exclusion 조건을 추가한 Top-K 빈도 집계 스크립트.
- 실제 입력 파일: `--scores` CSV, `--ranker` 컬럼, 선택적 `--exclude-col`.
- 실제 출력 파일: `--out` CSV (`panel_id`, `days_in_topk`, `share_days`).
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음.
- 현재 체인에서의 필요도: `moved to support`
- 판정 이유: `topk_workload.py`보다 기능이 명확히 많고, confirmed/final 패널 제외 같은 분석 옵션을 가진다. 활성 체인 직접 참조는 없어 `research/support/prognostics/`로 이동해도 runtime 영향이 없었다.
- 즉시 삭제하면 안 되는 파일: `아니오`

### 3) `research/support/prognostics/eval_topk.py`
- 현재 역할 한 줄 요약: 미래 손실 라벨(`future_loss_Hd`, `highloss_q`) 기준으로 Top-K capture/precision/workload를 평가하는 loss-based evaluator.
- 실제 입력 파일: `--in`으로 주는 loss label 포함 score CSV.
- 실제 출력 파일: `topk_daily_h{H}_k{K}.csv`, `topk_report_h{H}_k{K}.json`, 선택적 `leadtime_case_study.csv`.
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음.
- 현재 체인에서의 필요도: `moved to support`
- 판정 이유: fault onset 기반이 아니라 future-loss 기반 평가를 담당하므로 `eval_fault_topk_leadtime.py`와 역할이 다르다. 직접 활성 체인에 묶여 있지 않아 support 위치로 이동했다.
- 즉시 삭제하면 안 되는 파일: `아니오`

### 4) `research/support/prognostics/eval_fault_topk_leadtime.py`
- 현재 역할 한 줄 요약: fault event onset 기준으로 pre-window 안에서 ranker의 최초 Top-K 진입일과 leadtime을 계산하는 fault-based evaluator.
- 실제 입력 파일: `--scores` CSV, `--events` fault event CSV.
- 실제 출력 파일: `--out` CSV (`panel_id`, `ranker`, `k`, `first_topk_date`, `lead_days_topk` 등).
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음.
- 현재 체인에서의 필요도: `moved to support`
- 판정 이유: `eval_topk.py`와 달리 미래 손실이 아니라 실제 fault onset을 기준으로 리드타임을 계산한다. runtime caller가 없어 support 위치로 이동해도 안전했다.
- 즉시 삭제하면 안 되는 파일: `아니오`

### 5) `research/prognostics/compare_rankers.py`
- 현재 역할 한 줄 요약: 동일한 future loss 라벨 위에서 여러 ranking 컬럼의 capture/precision/lift를 비교하는 실험 스크립트.
- 실제 입력 파일: `--in` scores+loss CSV (`future_loss_Hd`, 선택적 `highloss_q` 포함), `--cols` ranker 목록.
- 실제 출력 파일: `--out` CSV (`rank_col`, `k`, `mean_capture_rate`, `mean_precision_at_k`, `lift_vs_base` 등).
- 직접 호출하는 파일 또는 호출되는 위치: `make_loss_labels.py` 산출(`highloss_q`, `future_loss_Hd`)에 직접 의존. 코드 내부에 `Re-run make_loss_labels.py first.` 문구가 있다.
- 현재 체인에서의 필요도: `support`
- 판정 이유: 활성 메인 체인에는 직접 묶여 있지 않지만, ranker 비교 실험의 중심 파일이다. `make_loss_labels.py`와 짝을 이루므로 실험 체인 보존 가치가 있다.
- 즉시 삭제하면 안 되는 파일: `예`

### 6) `research/prognostics/make_loss_labels.py`
- 현재 역할 한 줄 요약: panel-day risk CSV에 future loss 연속값과 `highloss_q` 이진 라벨을 추가하는 라벨 생성기.
- 실제 입력 파일: `--in` panel-day score CSV, 기본적으로 `panel_day_risk.csv` 계열.
- 실제 출력 파일: `--out` CSV (입력 컬럼 + `daily_loss`, `future_loss_{H}d`, `highloss_thr`, `highloss_q`).
- 직접 호출하는 파일 또는 호출되는 위치: `compare_rankers.py`가 `highloss_q`가 없으면 재실행을 요구한다.
- 현재 체인에서의 필요도: `support`
- 판정 이유: 메인 운영 체인은 아니지만 loss-based 평가 실험의 라벨 SSOT 역할을 한다. downstream 실험이 실제로 의존하므로 archive/remove로 바로 보내면 안 된다.
- 즉시 삭제하면 안 되는 파일: `예`

### 7) `research/archive/prognostics/make_fault_case_plots.py`
- 현재 역할 한 줄 요약: fault event CSV를 기준으로 패널별 타임라인 CSV/PNG를 생성하는 단순 case plotter.
- 실제 입력 파일: `--scores` CSV, `--events` fault event CSV.
- 실제 출력 파일: `case_<panel>.csv`, `case_<panel>.png` in `--out-dir`.
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음.
- 현재 체인에서의 필요도: `archived`
- 판정 이유: `plot_fault_cases_v2.py`가 더 명시적인 score set과 onset/diagnosis 선 표시를 포함해 paper pack 쪽에서 실제로 사용된다. 이 파일은 기능이 겹치고 직접 호출 흔적도 없어 1차 정리에서 archive로 이동했다.
- 즉시 삭제하면 안 되는 파일: `아니오`

### 8) `research/prognostics/plot_fault_cases_v2.py`
- 현재 역할 한 줄 요약: fault event 기반 case window CSV/PNG를 생성하는 현재형 paper-pack case plot 스크립트.
- 실제 입력 파일: `--scores` CSV, `--events` CSV (`onset_date` 또는 `fault_segment_start`, 선택적 `diagnosis_date`).
- 실제 출력 파일: `case_<panel>.csv`, `case_<panel>.png` in `--out-dir`.
- 직접 호출하는 파일 또는 호출되는 위치: `run_paper_pack.sh`에서 직접 호출된다.
- 현재 체인에서의 필요도: `keep`
- 판정 이유: review 대상 중 유일하게 현재 지원 체인(shell)에서 직접 호출되는 case plotter다. 실제 보고 체인과 연결된 파일이라 즉시 삭제 대상이 아니다.
- 즉시 삭제하면 안 되는 파일: `예`

### 9) `pv_ae/archive/scan_baseline.py`
- 현재 역할 한 줄 요약: 날짜 범위 raw CSV를 스캔하며 baseline 적합도를 요약하는 엔진 인접 실험 스크립트.
- 실제 입력 파일: `--dir` raw CSV 디렉터리, `--pattern`, `--start`, `--end`.
- 실제 출력 파일: `<data_dir>/baseline_scan_daily.csv`.
- 직접 호출하는 파일 또는 호출되는 위치: 현재 소스 트리에서 직접 호출 흔적 없음. 내부적으로 `pv_autoencoder_dayAE.compute_event_features`를 import한다.
- 현재 체인에서의 필요도: `archived`
- 판정 이유: core 엔진 함수를 재사용하지만 현재 실행 체인에 직접 묶여 있지는 않다. baseline 진단 실험의 흔적으로 보여 1차 정리에서 archive로 이동했다.
- 즉시 삭제하면 안 되는 파일: `아니오`

## Difference Notes

### `topk_workload.py` vs `topk_workload2.py`
- `topk_workload.py`는 날짜별 Top-K 빈도만 계산하는 최소 버전이다.
- `topk_workload2.py`는 `--exclude-col`, `--exclude-true`를 지원해 이미 fault/final 패널을 제외한 집계를 할 수 있다.
- 따라서 둘 중 유지 우선순위는 `topk_workload2.py`가 높고, `topk_workload.py`는 archive 쪽에 가깝다.

### `eval_topk.py` vs `eval_fault_topk_leadtime.py`
- `eval_topk.py`는 `future_loss_{H}d`, `highloss_q`를 이용한 loss-based capture/precision/workload 평가기다.
- `eval_fault_topk_leadtime.py`는 실제 `onset_date` 이전에 Top-K에 언제 들어오는지 보는 fault-based leadtime 평가기다.
- 즉, 둘은 비슷해 보이지만 타깃 정의가 다르므로 중복 파일이 아니라 서로 다른 평가 프레임을 담당한다.

## Direct Link Checks

- `research/prognostics/run_paper_pack.sh` -> `research/prognostics/plot_fault_cases_v2.py`
- `research/prognostics/compare_rankers.py` -> `research/prognostics/make_loss_labels.py`

## Final Classification

### keep
- `research/prognostics/plot_fault_cases_v2.py`

### moved to support
- `research/support/prognostics/topk_workload2.py`
- `research/support/prognostics/eval_topk.py`
- `research/support/prognostics/eval_fault_topk_leadtime.py`

### support
- `research/prognostics/compare_rankers.py`
- `research/prognostics/make_loss_labels.py`

### archived
- `research/archive/prognostics/topk_workload.py`
- `research/archive/prognostics/make_fault_case_plots.py`
- `pv_ae/archive/scan_baseline.py`

### remove candidate
- 없음. 현재 기준으로는 중복/비활성 흔적은 있어도 즉시 삭제까지 확정할 증거는 부족하다.
