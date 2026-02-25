# Refactor Audit: `pv_autoencoder_dayAE_v2.py` vs `pv_ae/pv_autoencoder_dayAE.py`

## 0) 범위/전제
- 비교 대상
  - 현재 운영 파일: `pv_ae/pv_autoencoder_dayAE.py` (2829 lines)
  - 비교 기준(v2): `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py` (1827 lines)
- 이번 문서 목적: **동작 변경 없이 정리 가능한 리팩터 후보(A)**와, **동작 변경 위험(B)**, **누락/삭제 위험(C)**를 분리해 안전한 이식 계획만 제시.
- 제약: 본 단계는 코드 수정/커밋 없이 감사 보고서만 작성.

## 1) 차이 분류표 (A/B/C)

### A. 안전한 리팩터(동작 동일 목표)
| ID | 항목 | 현재 코드 근거 | v2 코드 근거 | 안전 판단 근거 |
|---|---|---|---|---|
| A1 | 경로/파일선별 블록 함수화 (`_setup_paths`) | `pv_ae/pv_autoencoder_dayAE.py:1281`, `pv_ae/pv_autoencoder_dayAE.py:1343`, `pv_ae/pv_autoencoder_dayAE.py:1366` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:917` | 로직 자체는 동일(입력 경로, date range 필터, train/eval 파일 분리). 코드 위치만 이동 가능. |
| A2 | V-ref/V-drop 계산 블록 함수화 (`_compute_vref_merge`) | `pv_ae/pv_autoencoder_dayAE.py:1582`, `pv_ae/pv_autoencoder_dayAE.py:1660`, `pv_ae/pv_autoencoder_dayAE.py:1785` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:991` | 수식/파라미터 유지 전제에서 함수 추출만 수행 가능. |
| A3 | group-off 탐지 블록 함수화 (`_detect_group_off`) | `pv_ae/pv_autoencoder_dayAE.py:1872`, `pv_ae/pv_autoencoder_dayAE.py:1927`, `pv_ae/pv_autoencoder_dayAE.py:1936` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1099` | `(date, group_key)` 후보→Jaccard 확정→`group_off_like` 생성 흐름이 동일. |
| A4 | streak 계산 공통화 (`compute_run_streak`) | `pv_ae/pv_autoencoder_dayAE.py:1962`, `pv_ae/pv_autoencoder_dayAE.py:1985`, `pv_ae/pv_autoencoder_dayAE.py:2452` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:120` | dead/critical/EWS 모두 동일 패턴 반복. helper 치환은 동작 동일 리팩터 후보. |
| A5 | EWS 계산 블록 함수화 (`_compute_ews`) | `pv_ae/pv_autoencoder_dayAE.py:2351`, `pv_ae/pv_autoencoder_dayAE.py:2373`, `pv_ae/pv_autoencoder_dayAE.py:2467` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1170` | causal(`past = out[date < d]`) 규칙만 보존하면 안전. |
| A6 | site-event 계산 블록 함수화 (`_compute_site_events`) | `pv_ae/pv_autoencoder_dayAE.py:2477`, `pv_ae/pv_autoencoder_dayAE.py:2510`, `pv_ae/pv_autoencoder_dayAE.py:2531` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1247` | soft/hard 조건과 reason 생성 로직이 동일. |
| A7 | 리포트 저장 중복 축소 (`_safe_report_write`) | `pv_ae/pv_autoencoder_dayAE.py:2169`, `pv_ae/pv_autoencoder_dayAE.py:2674`, `pv_ae/pv_autoencoder_dayAE.py:2797` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:144`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1767` | 동일 파일 저장 반복을 공통 헬퍼로 줄여도 산출물은 동일하게 유지 가능. |
| A8 | event feature 기본값 매핑 공통화 (`_EV_DEFAULTS`) | `pv_ae/pv_autoencoder_dayAE.py:1470`~`pv_ae/pv_autoencoder_dayAE.py:1491` (개별 필드 수동 추출) | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1308`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1421` | 동일 키/기본값을 유지하면 코딩량만 감소. 단, 타입 캐스팅 보존 필요(아래 B4 참조). |

### B. 동작 변경 가능(위험)
| ID | 위험 항목 | 현재 코드 근거 | v2 코드 근거 | 위험 설명 |
|---|---|---|---|---|
| B1 | v_ref merge 충돌 대응 축소 위험 | `pv_ae/pv_autoencoder_dayAE.py:1611`, `pv_ae/pv_autoencoder_dayAE.py:1715`, `pv_ae/pv_autoencoder_dayAE.py:1723` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1059` | 현재는 `_x/_y` merge artifact 정리와 span 후보 선택 로직이 있음. 단순 치환 시 재실행/재병합 환경에서 결과 달라질 수 있음. |
| B2 | `n_total` 컬럼 순서/삽입 방식 차이 | `pv_ae/pv_autoencoder_dayAE.py:2309`, `pv_ae/pv_autoencoder_dayAE.py:2336` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1321` | 현재는 동적 삽입(방어적), v2는 정적 리스트. 헤더 순서 및 일부 다운스트림 파서가 영향받을 수 있음. |
| B3 | 예외 처리 강도 변경 위험 | `pv_ae/pv_autoencoder_dayAE.py:2102` (panel diagnosis 저장은 hard-fail 성격) | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1590` (`_safe_report_write`) | 저장 실패를 경고로만 넘기면 실패 감지가 지연될 수 있음. |
| B4 | event feature 타입 캐스팅 방식 차이 | `pv_ae/pv_autoencoder_dayAE.py:1470`~`pv_ae/pv_autoencoder_dayAE.py:1491` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1422` | v2의 generic 캐스팅은 입력값 타입 이상치에서 현재와 다르게 변환될 수 있음(특히 bool/int/float 혼합). |
| B5 | 정렬 시점 이동 위험 | `pv_ae/pv_autoencoder_dayAE.py:1962`, `pv_ae/pv_autoencoder_dayAE.py:2608`, `pv_ae/pv_autoencoder_dayAE.py:2615` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1519`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1724`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1806` | streak/rolling/groupby min 결과는 정렬 시점이 바뀌면 달라질 수 있음. |
| B6 | bool/NaN 해석 차이 위험 | `pv_ae/pv_autoencoder_dayAE.py:395`~`pv_ae/pv_autoencoder_dayAE.py:399` | `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:361`~`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:365` | 현재는 NaN→False를 강제하는 방어가 중요. helper 이식 시 이 규칙 깨지면 `v_ref_ok/data_bad/group_off_like` 영향 큼. |

### C. 누락/삭제 위험 (핵심 로직/출력)
| ID | 점검 항목 | 현재 | v2 | 판정 |
|---|---|---|---|---|
| C1 | `v_drop` 생성/활용 | 있음 (`pv_ae/pv_autoencoder_dayAE.py:1785`, `pv_ae/pv_autoencoder_dayAE.py:1953`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1084`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1514`) | **누락 없음** |
| C2 | `diagnosis_date_online` 생성 | 있음 (`pv_ae/pv_autoencoder_dayAE.py:2074`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1572`) | **누락 없음** |
| C3 | `final_fault` 생성 | 있음 (`pv_ae/pv_autoencoder_dayAE.py:2032`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1552`) | **누락 없음** |
| C4 | `ews_warning` 생성/게이트 | 있음 (`pv_ae/pv_autoencoder_dayAE.py:2467`, `pv_ae/pv_autoencoder_dayAE.py:2536`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1241`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1686`) | **누락 없음** |
| C5 | `prefault_B` 생성 | 있음 (`pv_ae/pv_autoencoder_dayAE.py:2655`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1741`) | **누락 없음** |
| C6 | panel diagnosis 출력(`ae_simple_panel_diagnosis.csv`) | 있음 (`pv_ae/pv_autoencoder_dayAE.py:2101`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:1590`) | **누락 없음** |
| C7 | critical SSOT 컬럼 (`critical_like_eff`, `critical_source`) | 있음 (`pv_ae/pv_autoencoder_dayAE.py:459`, `pv_ae/pv_autoencoder_dayAE.py:474`) | 있음 (`/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:404`, `/Users/b9gc/Downloads/pv_autoencoder_dayAE_v2.py:415`) | **누락 없음** |

> 결론(C): 요청하신 핵심 항목(EWS/prefault/v_drop/diagnosis_date_online/final_fault) 기준으로 **v2에서 사라진 코어 로직은 확인되지 않음**. 다만 B1~B6의 구현 세부 차이로 인해 이식 과정에서 동작이 바뀔 위험은 큼.

## 2) A(안전)만 대상으로 한 커밋 단위 이식 계획 (제안)

### Commit A1: 경로/파일 선별 함수 추출
- 주제: `main()`의 경로/입력 파일 선별 블록을 `_setup_paths(args)`로 분리.
- 범위: `pv_ae/pv_autoencoder_dayAE.py:1281`~`pv_ae/pv_autoencoder_dayAE.py:1391`
- 비기능 목표: 가독성 개선, 테스트 포인트 분리.
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. 동일 옵션 baseline/candidate 실행 후 `ae_simple_scores.csv` 생성 확인

### Commit A2: streak 공통화(helper 치환)
- 주제: dead/critical/EWS 3개 루프를 `compute_run_streak()`로 통일.
- 범위: `pv_ae/pv_autoencoder_dayAE.py:1962`~`pv_ae/pv_autoencoder_dayAE.py:1975`, `pv_ae/pv_autoencoder_dayAE.py:1985`~`pv_ae/pv_autoencoder_dayAE.py:1997`, `pv_ae/pv_autoencoder_dayAE.py:2452`~`pv_ae/pv_autoencoder_dayAE.py:2464`
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. 핵심 컬럼 true count 동일성 비교(`dead_streak`, `crit_streak`, `ews_warning`)

### Commit A3: group-off 탐지 함수 추출
- 주제: group-off 후보/확정/게이트 블록을 `_detect_group_off(out,args)`로 분리.
- 범위: `pv_ae/pv_autoencoder_dayAE.py:1872`~`pv_ae/pv_autoencoder_dayAE.py:1943`
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. `group_off_like`, `state_dead_eff`, `v_drop` NaN count 동일 비교

### Commit A4: EWS + site-event 함수 추출
- 주제: EWS 계산과 site-event 게이트를 `_compute_ews`, `_compute_site_events`로 분리.
- 범위: `pv_ae/pv_autoencoder_dayAE.py:2351`~`pv_ae/pv_autoencoder_dayAE.py:2539`
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. `ews_*`, `ews_warning`, `site_event_*` 컬럼 동일성 비교

### Commit A5: 리포트 저장 중복 축소
- 주제: `_safe_report_write` 도입으로 반복 `to_csv` 블록 축소(산출물/파일명 유지).
- 범위: `pv_ae/pv_autoencoder_dayAE.py:2169`~`pv_ae/pv_autoencoder_dayAE.py:2172`, `pv_ae/pv_autoencoder_dayAE.py:2674`~`pv_ae/pv_autoencoder_dayAE.py:2797`
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. 기존 산출 파일 존재성 + 헤더 비교

### Commit A6: event 기본값 매핑 공통화(선택)
- 주제: 수동 필드 추출을 `_EV_DEFAULTS` 기반으로 축약.
- 주의: B4 위험 항목(타입 캐스팅 차이) 때문에 **가장 마지막**에 수행.
- 회귀검증
  1. `python -m py_compile pv_ae/pv_autoencoder_dayAE.py`
  2. `mid_ratio`, `coverage_mid`, `seg_count`, `recovered_sustained` 타입/결측률 비교

## 3) 회귀검증(필수) 제안

### 3-1. baseline/candidate 실행 커맨드 (동일 옵션)
아래에서 `BASE_SCRIPT`와 `CAND_SCRIPT`만 바꾸고 **나머지 옵션은 완전히 동일**하게 고정:

```bash
# 예시: wrapper 사용 (동일 옵션 강제하기 쉬움)
python research/prognostics/run_dayae_site.py --site kernelog1 --train-days 60

# 또는 직접 실행 시
python pv_ae/pv_autoencoder_dayAE.py \
  --site kernelog1 \
  --train-start <YYYY-MM-DD> --train-end <YYYY-MM-DD> \
  --eval-start <YYYY-MM-DD> --eval-end <YYYY-MM-DD> \
  <기타 옵션 동일>
```

권장 운영 방식:
- baseline 결과를 `data/kernelog1/out/ae_simple_scores.baseline.csv`
- candidate 결과를 `data/kernelog1/out/ae_simple_scores.candidate.csv`
로 분리 저장 후 비교.

### 3-2. 핵심 컬럼 동등성 비교 스크립트 (요구 반영)
비교 대상 컬럼:
- `mid_ratio`, `state_dead_eff`, `dead_streak`, `diagnosis_date_online`, `final_fault`, `v_drop`, `critical_like_eff`

```python
import pandas as pd

base = pd.read_csv("data/kernelog1/out/ae_simple_scores.baseline.csv")
cand = pd.read_csv("data/kernelog1/out/ae_simple_scores.candidate.csv")

for df in (base, cand):
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()

key = ["date", "panel_id"]
cols = ["mid_ratio", "state_dead_eff", "dead_streak", "diagnosis_date_online", "final_fault", "v_drop", "critical_like_eff"]

# 1) 행수
print("rows", len(base), len(cand), "equal=", len(base)==len(cand))

# 2) True count / non-null count
for c in cols:
    if c in ["state_dead_eff", "final_fault", "critical_like_eff"]:
        bt = pd.to_numeric(base[c], errors="coerce").fillna(0).astype(int).sum()
        ct = pd.to_numeric(cand[c], errors="coerce").fillna(0).astype(int).sum()
        print(c, "true_count", bt, ct, "equal=", bt==ct)
    else:
        bn = base[c].notna().sum()
        cn = cand[c].notna().sum()
        print(c, "notna", bn, cn, "equal=", bn==cn)

# 3) key join 값 비교
m = base[key + cols].merge(cand[key + cols], on=key, suffixes=("_b","_c"), how="inner")
for c in cols:
    b = m[f"{c}_b"]
    d = m[f"{c}_c"]
    if c in ["diagnosis_date_online"]:
        b = pd.to_datetime(b, errors="coerce").dt.normalize()
        d = pd.to_datetime(d, errors="coerce").dt.normalize()
    else:
        b = pd.to_numeric(b, errors="coerce")
        d = pd.to_numeric(d, errors="coerce")
    neq = (~(b.fillna(-999999) == d.fillna(-999999))).sum()
    print(c, "diff_rows", int(neq))

# 4) 1.1 / 2.0 케이스 진단일 비교
for suffix in [".1.1", ".2.0"]:
    b_sub = base[base["panel_id"].astype(str).str.endswith(suffix)]
    c_sub = cand[cand["panel_id"].astype(str).str.endswith(suffix)]
    if b_sub.empty or c_sub.empty:
        print(suffix, "panel not found in one side")
        continue

    pid = sorted(set(b_sub["panel_id"]).intersection(set(c_sub["panel_id"])))
    if not pid:
        print(suffix, "common panel not found")
        continue
    pid = pid[0]

    b_diag = pd.to_datetime(b_sub.loc[b_sub["panel_id"]==pid, "diagnosis_date_online"], errors="coerce").min()
    c_diag = pd.to_datetime(c_sub.loc[c_sub["panel_id"]==pid, "diagnosis_date_online"], errors="coerce").min()
    print("case", suffix, "pid", pid, "diag_base", b_diag, "diag_cand", c_diag, "equal=", b_diag==c_diag)
```

## 4) 공격 포인트(동작 바뀜 가능성) 우선순위
1. **B1 (최우선)**: v_ref merge 아티팩트 처리 축소 시 `v_ref_ok`/`v_drop`가 바뀔 가능성.
2. **B5**: 정렬 시점 이동으로 `dead_streak`, `crit_streak`, `diagnosis_date_online` 변동 가능.
3. **B4/B6**: 타입·결측 처리 변경 시 bool 게이트(`data_bad`, `group_off_like`, `v_ref_ok`)가 틀어질 수 있음.
4. **B3**: 저장 에러 은닉 시 재현 실패를 늦게 발견.

## 5) 재현 커맨드 기록 (AGENTS.md 규칙)
- 변경 전(베이스라인 산출):
  - `python research/prognostics/run_dayae_site.py --site kernelog1 --train-days 60`
- 변경 후(후보 산출, 동일 옵션):
  - `python research/prognostics/run_dayae_site.py --site kernelog1 --train-days 60`
- 비교:
  - 위 `3-2` 스크립트 실행

---
판정 요약:
- **즉시 이식 가능한 안전 리팩터(A)**는 충분히 존재한다.
- 단, 실제 공격 포인트는 대부분 **v_ref/v_drop merge 안정성(B1)**과 **정렬/결측/타입 처리(B4~B6)**에서 발생한다.
- 따라서 커밋 순서는 A1→A5 순으로 작은 단위로 진행하고, A6는 마지막에 분리하는 것이 안전하다.
