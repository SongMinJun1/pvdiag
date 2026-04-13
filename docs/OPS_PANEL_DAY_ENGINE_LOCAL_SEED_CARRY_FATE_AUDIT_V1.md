# OPS_PANEL_DAY_ENGINE_LOCAL_SEED_CARRY_FATE_AUDIT_V1

## 왜 direct adjudication 대신 retrospective fate를 보나
- `current_seed_carry1` unmatched run은 수가 많고, 전부 수작업 adjudication으로 보기는 비효율적이다.
- 그래서 같은 패널의 이후 7/30/60일 경과를 보고, 나중에 실제 fault/truth/recurrence로 이어졌는지를 proxy로 본다.
- 이건 detector를 바꾸는 단계가 아니라, detector-side refinement를 계속 밀어도 되는지 판단하는 audit 단계다.

## 각 fate_class 의미
- `future_fault_linked`
  - run 종료 뒤 30~60일 내 같은 패널에서 `confirmed_fault`, `critical_fault`, `final_fault` 가 나온 경우
- `future_truth_linked`
  - fault flag는 없지만 30~60일 내 같은 패널 truth row가 다시 붙는 경우
- `recurring_chronic_monitor_like`
  - fault/truth는 없지만 60일 내 같은 패널에서 pre_alarm run이 다시 생겨 chronic monitor burden처럼 보이는 경우
- `isolated_unexplained`
  - fault, truth, recurrence 모두 없이 고립된 burden으로 남는 경우

## 왜 이게 다음 proxy로 맞나
- direct adjudication은 느리고 coverage가 작다.
- retrospective fate는 detector가 숨은 positive를 미리 잡고 있었는지, 아니면 chronic burden만 늘리는지 빠르게 가늠하게 해준다.

## 어떤 결과가 다음 결정을 정당화하나
- A) `seed_carry1` 이 hidden value를 찾는다고 볼 근거
  - `future_fault_linked + future_truth_linked` 비율이 높고 chronic run에서도 반복되면 detector가 실제 후행 사건을 먼저 잡고 있을 가능성이 크다.
- B) `seed_carry1` 이 mainly chronic monitor burden이라고 볼 근거
  - fault/truth linkage는 낮고 `recurring_chronic_monitor_like` 가 높으면 operator-facing consolidation 문제에 더 가깝다.
- C) detector refinement를 멈출 근거
  - `isolated_unexplained` 비율이 높고 fault/truth/recurrence 근거가 약하면 detector-side 추가 수정은 멈추는 편이 낫다.

