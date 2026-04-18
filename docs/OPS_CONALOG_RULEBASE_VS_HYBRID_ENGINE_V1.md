# OPS Conalog Rulebase Vs Hybrid Engine V1

## 1. 비교 목적
- conalog rulebase와 hybrid engine의 역할 차이를 운영 관점에서 정리하기 위한 초안임.

## 2. 입력 데이터 범위 차이
- conalog는 현재 운영 데이터와 직접 연결된 direct operational interpretation layer임.
- hybrid engine은 추가 reference layer를 함께 읽는 구조를 가질 수 있음.

## 3. 탐지/판정 구조 차이
- conalog는 규칙 기반 운영 판독 흐름이 중심임.
- hybrid engine은 panel multiaxis verdict, GPVS, heuristic 등 보조층을 함께 조합할 수 있음.

## 4. 설명 가능성 차이
- conalog는 현장 설명과 운영 판단에 바로 연결되기 쉬움.
- hybrid engine은 설명량은 늘지만 layer 간 구분을 분명히 해야 함.

## 5. conalog와 GPVS 사용 위치
- conalog는 direct operational interpretation layer임.
- GPVS는 reference-only 보조층이며 direct root-cause classifier가 아님.

## 6. root-cause 확정 가능 여부
- 현재 어느 쪽도 자동으로 최종 root-cause를 확정한다고 읽으면 안 됨.

## 7. 현장 triage 지원 차이
- conalog는 운영 경보와 직접 대응에 유리함.
- hybrid engine은 candidate narrowing과 설명 보강에 유리할 수 있음.

## 8. 현재 결론
- 현재 primary는 panel multiaxis verdict와 conalog이며, GPVS와 heuristic은 보조층으로만 사용함.
