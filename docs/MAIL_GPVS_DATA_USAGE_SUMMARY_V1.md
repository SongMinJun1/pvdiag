# 제목
- GPVS 데이터 사용 범위 및 현재 운영 해석 원칙 공유

# 수신 대상 가정 문구
- 수신 대상은 현재 conalog 기반 운영 결과를 검토하거나 외부 전달용 설명자료를 확인하는 실무/검토 담당자라고 가정하였음.

# 본문
현재 프로젝트에서 GPVS 데이터와 산출물의 사용 위치를 혼동하지 않도록 현재 운영 원칙을 아래와 같이 정리하여 공유함.

현재 스택의 primary 판정층은 panel multiaxis verdict 임. conalog는 direct operational interpretation layer 로 사용 중임. GPVS는 외부 실험 자산을 활용한 reference-only 보조층이며, heuristic은 field-trial triage-only 후보 축소층으로만 사용 중임.

중요한 점은 GPVS를 direct classifier처럼 읽으면 안 된다는 점임. 현재 GPVS는 외부 실험 시나리오와 닮은 reference pattern을 설명하는 용도로는 유의미하나, 실제 패널의 최종 물리 root-cause를 단독으로 확정하는 direct root-cause classifier는 아님. current evidence summary 기준으로도 compatibility_reference_only_flag=1 이며, 운영 원칙 문구는 “GPVS는 direct root-cause classifier가 아니라 reference layer로만 사용”으로 고정되어 있음.

현재 frozen sample 기준 GPVS 사용 결과는 core reference 2건, auxiliary reference 4건으로 정리되어 있음. 이는 GPVS가 완전히 비활성화된 층이 아니라 설명 보강과 triage 보조에는 실제로 사용되고 있음을 뜻함. 다만 이 사용은 어디까지나 reference-only 범위이며, conalog나 panel multiaxis verdict를 대체하는 primary 판단으로 승격하지 않음.

정리하면 현재 역할 분담은 다음과 같음.  
panel multiaxis verdict = primary  
conalog = direct operational interpretation layer  
GPVS = reference-only  
heuristic = triage-only

따라서 외부 설명이나 운영 전달 시에는 stable default output을 우선하고, GPVS와 heuristic은 반드시 보조층으로 분리하여 설명하는 것이 적절함. GPVS scenario/family 정보를 direct diagnosis처럼 번역하거나, heuristic ranking을 최종 원인 확정처럼 해석하는 것은 현재 공식 운영 원칙과 맞지 않음.

필요 시 별도 문서로는 GPVS external data inventory, conalog rulebase vs hybrid engine 비교 문서, runtime readiness 문서를 함께 전달할 수 있음.

# 핵심 요약 3줄
- panel multiaxis verdict가 primary 이고, conalog는 direct operational interpretation layer 임.
- GPVS는 reference-only 이며 direct classifier처럼 읽으면 안 됨.
- heuristic은 triage-only 이므로 최종 진단값이 아니라 현장 후보 축소층으로만 사용함.
