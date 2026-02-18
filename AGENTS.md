# pvdiag 협업 규칙 (Codex)

프로젝트 목표
- PV 패널 전조/예측(early warning)과 확정 진단(confirmed fault)을 분리한 파이프라인을 재현 가능하게 유지한다.
- 논문/발표 방어가 가능하도록, 정의(라벨/지표/평가)를 문서로 남긴다.

작업 규칙 (필수)
- 작업 시작 전/후 git status 확인
- 변경 전후 재현 커맨드 1개씩 기록
- 의미 없는 대규모 포맷팅/리네이밍 금지
- 알고리즘 동작 변경 시: paper_pack/ONEPAGER.md 또는 data_dictionary_paper.md 업데이트 필수
- data/<site>/raw, data/<site>/out 대용량 데이터는 커밋/번들에 기본 포함하지 않는다(필요 시 샘플만)

검증 최소 조건
- python -m py_compile pv_ae/pv_autoencoder_dayAE.py
- kernelog1 1회 실행 또는 paper_pack 재생성 스크립트 성공 확인

완료 보고 형식
- 변경 파일 목록
- 동작 변경 여부(있/없)
- 재현 커맨드
- 산출물 경로
