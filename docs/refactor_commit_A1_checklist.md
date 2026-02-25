# Commit A1 실행 체크리스트 (계획 전용)

## 1) A1 목표 (한 문장)
- Commit A1의 목표는 `main()`의 경로/파일선별 블록을 `_setup_paths(args)`로 **동작 동일하게 함수 분리**하는 리팩터를 수행하는 것이다.

## 2) 변경 파일/함수 목록 (정확 범위)
- 변경 파일: `pv_ae/pv_autoencoder_dayAE.py`
- 신규 함수(예정): `_setup_paths(args)`  
  현재 `main()` 내부 경로/파일선별/범위필터/디렉토리 준비 블록을 이 함수로 이동
- 수정 함수(예정): `main()`
  - 대상 블록(현행 기준): `pv_ae/pv_autoencoder_dayAE.py:1281`~`pv_ae/pv_autoencoder_dayAE.py:1391`
  - 내용: 인라인 경로 계산/파일선별 코드를 제거하고 `_setup_paths(args)` 호출로 대체
- 변경 금지 파일:
  - `research/prognostics/*`
  - `docs/*` (본 체크리스트 제외)
  - 데이터/출력 CSV 파일

## 3) 절대 하면 안 되는 것 (비목표)
- 임계값 변경 금지 (`--v-drop-thr`, `--dead-days`, `--critical-days`, `--coverage-min` 등 전부 유지)
- 필터 조건 변경 금지 (train/eval date range, 파일 패턴, suffix/date 파싱 규칙 유지)
- 결측 처리 변경 금지 (`fillna`, `to_numeric`, NaN/NaT 처리 방식 유지)
- 정렬 변경 금지 (`sort_values` 위치/키 변경 금지)
- 그룹키 변경 금지 (`panel_group_key`, `group_key`, `group_key_ref`, `vbin` 처리 유지)
- 출력 컬럼/순서 변경 금지 (`OUT_COLS`, 저장 파일명, CSV 헤더 유지)
- 라벨 로직 변경 금지 (`state_dead_eff`, `critical_like_eff`, `final_fault`, `diagnosis_date_online` 계산식 불변)
- 후처리 연계 변경 금지 (`ae_simple_scores.csv` 위치/이름 유지)

## 4) 성공 판정 기준(회귀 기준) 10개
- [ ] 1.1 케이스 날짜 동일: `dead_start_date=2025-03-21`
- [ ] 1.1 케이스 날짜 동일: `diagnosis_date_online=2025-03-22`
- [ ] 1.1 케이스 지연 동일: `delay_days=2`
- [ ] 2.0 케이스 날짜 동일: `dead_start_date=2025-12-18`
- [ ] 2.0 케이스 날짜 동일: `diagnosis_date_online=2025-12-19`
- [ ] 2.0 케이스 지연 동일: `delay_days=1`
- [ ] `ae_simple_scores.csv` 행수 동일
- [ ] `final_fault == True` 개수 동일
- [ ] `critical_like_eff == True` 개수 동일
- [ ] `diagnosis_date_online` NaT 개수 동일 (가능하면 `ae_simple_panel_diagnosis.csv`의 `dead_diag_date/critical_diag_date/diagnosis_date_online/final_fault_first_date`도 동일 확인)

## 5) 적용 후 실행 커맨드 (한 줄씩)
- `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
- `python research/prognostics/fault_case_study.py --site kernelog1 --case "c42997a6-5881-47e7-9035-7de8a2673b54.1.1:2025-03-20,7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0:2025-12-18" --K 20`
- `rg -n "용어 정의|날짜 요약|Top-K|dead_start_date|diagnosis_date_online|delay_days|2025-03-21|2025-03-22|2025-12-18|2025-12-19" data/kernelog1/out/CASE_STUDY_KERNELOG1.md`
- `python research/prognostics/plot_case_timeline.py --site kernelog1 --panel "c42997a6-5881-47e7-9035-7de8a2673b54.1.1" --onset 2025-03-20 --window 30`
- `python research/prognostics/plot_case_timeline.py --site kernelog1 --panel "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0" --onset 2025-12-18 --window 30`
- `ls -lh data/kernelog1/out/FIG_case_c42997a6-5881-47e7-9035-7de8a2673b54.1.1.png data/kernelog1/out/FIG_case_7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0.png`

## 6) 산출물
- 본 체크리스트 저장 위치: `docs/refactor_commit_A1_checklist.md`
- 본 문서는 계획 전용이며, 코드 변경/커밋을 포함하지 않는다.
