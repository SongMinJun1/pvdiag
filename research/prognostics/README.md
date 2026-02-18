# Prognostics (Risk / Hazard)

목표:
- scores.csv(panel×day)에서 risk score를 만들고,
- fault onset을 기준으로 horizon label을 만들고,
- P(fail within H days)를 출력하는 hazard 모델을 학습/평가한다.

파일:
- risk_score.py: risk_day/risk_7d/risk_30d/ews_score 생성
- make_labels.py: onset 기반 horizon label 생성(H=7/14/30)
- train_hazard.py: 로지스틱 기반 discrete-time hazard 학습/평가(필요시 sklearn)

실행 예시:
1) risk score 생성:
   python research/prognostics/risk_score.py --in ae_simple_scores.csv --out scores_with_risk.csv

2) 라벨 생성(이벤트 파일 있으면 더 정확):
   python research/prognostics/make_labels.py --in scores_with_risk.csv --out ds_h7.csv --horizon 7 --events fault_events.csv

3) hazard 학습:
   python research/prognostics/train_hazard.py --in ds_h7.csv --horizon 7
