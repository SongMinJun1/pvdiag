# pvdiag 협업 작업 티켓 (SSOT)

진행 규칙
- 모든 코드는 VS Code + Codex로 수정
- 변경은 브랜치/커밋 단위로 남김
- 변경 후 최소 검증: python -m py_compile + kernelog1 기준 산출 확인
- 논문 문장은 여기(ChatGPT)에서 작성, 결과표/그림은 코드 산출물로 고정

Phase 1 (필수 패치)
- [ ] P1-1 online 진단 시점 컬럼 추가 (dead_diag_date 등) + 출력 CSV에 포함
- [ ] P1-2 final_fault / confirmed_fault / online diagnosis 정의 문서(ONEPAGER, 딕셔너리) 정합성 맞추기
- [ ] P1-3 kernelog1 재실행 후 paper_pack 재생성, 표(events/leadtime/workload) 갱신

Phase 2 (논문 초안)
- [ ] P2-1 Methods 초안 (정규화/AE/DTW/HS/EWS/Rule, 평가 지표)
- [ ] P2-2 Experiments/Results 초안 (사건표/리드타임/워크로드/케이스 플롯)
- [ ] P2-3 Limitations + 방어 논리(라벨 적음, 일반화, 운영/검증 프레임)
