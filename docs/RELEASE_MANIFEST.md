# Release Manifest

## 1. release purpose

이번 배포의 목적은 재현 가능한 core pipeline과 그 후처리 체인을 명확한 경계로 묶는 것이다.

- 이 배포는 core pipeline 배포다.
- 실험 산출물 보고서 묶음은 부가 산출물이며, release bundle의 본체가 아니다.
- 보고서형 onepager, 내부 점검 문서, refactor 기록은 배포 번들에서 제외한다.

## 2. include in release

아래 파일은 현재 기준 release bundle 포함 대상이다.

- `README.md`
- `requirements.txt`
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
- `research/prognostics/run_dayae_site.py`
- `research/prognostics/README.md`
- `docs/DATA_DICTIONARY.md`
- `docs/score_definition.md`
- `docs/RELEASE_BOUNDARY.md`
- `docs/TESTED_ENVIRONMENT.md`
- `docs/RELEASE_MANIFEST.md`

## 3. keep in repo but exclude from release bundle

아래 파일은 레포에는 남기되, release bundle에는 넣지 않는다.

- `docs/reports/kernelog1_onepager.md`
- `docs/internal/WHAT_TO_LOOK_AT.md`
- `docs/internal/TASKS.md`
- `docs/internal/RESEARCH_ROADMAP.md`
- `docs/internal/refactor_audit_v2_vs_current.md`
- `docs/internal/refactor_commit_A1_checklist.md`
- `docs/archive/data_dictionary_paper_legacy.md`
- `docs/patches/` 이하 파일
- support/review 성격 스크립트:
  - `research/support/prognostics/topk_workload2.py`
  - `research/support/prognostics/eval_topk.py`
  - `research/support/prognostics/eval_fault_topk_leadtime.py`
  - `research/prognostics/compare_rankers.py`
  - `research/prognostics/make_loss_labels.py`
  - `research/prognostics/plot_fault_cases_v2.py`

## 4. exclude from repo tracking and release

아래는 레포 추적과 release bundle 모두에서 제외한다.

- `data/**`
- `_share/**`
- logs
- caches
- local tmp files

## 5. official output contract

공식 출력 파일명 계약은 아래 다섯 개다.

- `panel_day_core.csv`
- `panel_diagnosis_summary.csv`
- `panel_day_risk.csv`
- `panel_day_risk_transition.csv`
- `panel_day_risk_ensemble.csv`

## 6. minimum run sequence

최소 실행 순서는 아래와 같다.

1. core engine
   - 예: `python research/prognostics/run_dayae_site.py --site kernelog1`
2. post-processing
   - `python research/prognostics/run_scores_pipeline.py --site kernelog1`
3. optional site eval
   - `python research/prognostics/weaklabel_eval_2sigma.py --site kernelog1`
   - `python research/prognostics/fault_case_study.py --site kernelog1 --case "<panel_id>:<onset_date>"`
4. optional external benchmark
   - `python research/prognostics/ingest_gpvs_faults.py`
   - `python research/prognostics/external_eval_gpvs.py`
