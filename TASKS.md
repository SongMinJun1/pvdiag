# pvdiag 협업 작업 티켓 (SSOT)

진행 규칙
- 모든 코드는 VS Code + Codex로 수정
- 변경은 브랜치/커밋 단위로 남김
- 변경 후 최소 검증: python -m py_compile + kernelog1 기준 산출 확인
- 논문 문장은 여기(ChatGPT)에서 작성, 결과표/그림은 코드 산출물로 고정

Phase 1 (필수 패치: Commit A~E)
- [x] Commit A: 문서 SSOT 고정 (코드 변경 없음)
  - [x] ONEPAGER에 라벨/날짜 3분리, critical SSOT, rank_day 해석 주의 반영
  - [x] data_dictionary_paper 문서 신설/정리 + provenance(engine/postproc/eval) 명시
  - [x] 운영 Top-N 출력 vs 논문 leadtime/workload 지표 분리 명시
- [ ] Commit B: critical_like / v_ref / v_drop 계산 SSOT 단일화
  - [ ] compute_vdrop_labels(df, params) 중심으로 raw→effective 계산 단일 경로화
  - [ ] 중복/덮어쓰기 블록 축소 및 critical_source 추적성 정리
- [ ] Commit C: online 진단일 컬럼 추가
  - [ ] dead_diag_on_day/date, critical_diag_on_day/date, diagnosis_date_online 추가
  - [ ] ae_simple_panel_diagnosis.csv 생성
- [ ] Commit D: 출력 저장 지점 단일화
  - [ ] ae_simple_scores.csv 최종 저장 1회로 고정
  - [ ] 필요 시 debug 저장 분리 및 문서 명시
- [ ] Commit E: risk/transition/ensemble 생성 파이프라인 고정
  - [ ] run_scores_pipeline 엔트리 추가
  - [ ] scores_with_risk*.csv → scores_with_risk_transition.csv → scores_with_risk_ens*.csv 재현 절차 고정

Phase 2 (논문 초안)
- [ ] P2-1 Methods 초안 (정규화/AE/DTW/HS/EWS/Rule, 평가 지표)
- [ ] P2-2 Experiments/Results 초안 (사건표/리드타임/워크로드/케이스 플롯)
- [ ] P2-3 Limitations + 방어 논리(라벨 적음, 일반화, 운영/검증 프레임)
