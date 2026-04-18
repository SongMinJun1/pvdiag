# OPS GPVS External Data Inventory V1

## 1. 사용한 GPVS 자산
- 현재 프로젝트는 external GPVS 자산을 direct classifier가 아니라 reference layer로만 사용함.

## 2. recovered by-type artifact 현황
- recovered by-type artifact는 존재 여부와 provenance를 audit 문서 기준으로 따로 관리함.

## 3. GPVS를 direct classifier로 쓰지 않는 이유
- GPVS original scenario space와 MLPE official problem-type space가 동일하지 않기 때문임.
- 따라서 detailed code를 direct root-cause로 번역하면 안 됨.

## 4. 현재 reference-only 사용 원칙
- panel multiaxis verdict가 primary임.
- conalog는 direct operational interpretation layer임.
- GPVS는 reference-only 보조층임.
