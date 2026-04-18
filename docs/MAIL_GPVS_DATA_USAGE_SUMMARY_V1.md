# 제목
- GPVS 데이터 사용 위치 및 운영 해석 원칙 요약

# 본문
안녕하세요.

현재 프로젝트에서 GPVS는 panel multiaxis verdict를 대체하는 직접 판정기가 아니라 reference-only 보조층으로 사용 중임. 따라서 GPVS 출력은 direct root-cause classifier로 읽으면 안 되며, 외부 실험 시나리오와 닮은 reference pattern으로만 해석해야 함.

현재 역할 분담은 다음과 같음. panel multiaxis verdict가 최종 primary 판정층임. conalog는 direct operational interpretation layer임. GPVS는 reference-only 보조층임. heuristic cause candidate는 field-trial triage를 위한 후보 축소층임.

정리하면 GPVS는 운영 설명과 후보 축소를 돕는 참고축으로는 유의미하나, 단독으로 최종 root-cause를 확정하는 용도로 사용하지 않음. 관련 provenance, compatibility, matching 근거는 별도 evidence/audit 문서 기준으로 관리 중임.

# 핵심 요약 3줄
- GPVS는 reference-only 보조층임.
- GPVS를 direct root-cause classifier로 읽으면 안 됨.
- 현재 역할 분담은 panel multiaxis verdict / conalog / GPVS / heuristic 순으로 구분하여 운영 중임.
