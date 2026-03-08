import argparse, pandas as pd, numpy as np

def parse():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--ranker", required=True)
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude-col", default=None, help="e.g., final_fault")
    ap.add_argument("--exclude-true", action="store_true", help="exclude rows where exclude-col evaluates True")
    return ap.parse_args()

def to_bool(s):
    return s.astype(str).str.lower().isin(["1","true","t","yes"])

def main():
    a=parse()
    df=pd.read_csv(a.scores, low_memory=False, encoding="utf-8-sig")
    df["date"]=pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df["panel_id"]=df["panel_id"].astype(str)

    if a.exclude_col and a.exclude_col in df.columns and a.exclude_true:
        mask = ~to_bool(df[a.exclude_col])
        df = df[mask].copy()

    v=pd.to_numeric(df.get(a.ranker, np.nan), errors="coerce")
    df=df[v.notna()].copy()
    df["_v"]=v[v.notna()].astype(float)

    picked=[]
    for d,g in df.groupby("date", sort=True):
        g=g.sort_values("_v", ascending=False).head(a.k)
        picked.append(g[["panel_id"]].assign(date=d))
    pick=pd.concat(picked, ignore_index=True)

    freq=pick.groupby("panel_id").size().reset_index(name="days_in_topk")
    n_days=pick["date"].nunique()
    total = int(n_days * a.k)
    freq["share_days"]=freq["days_in_topk"]/max(1,n_days)
    freq=freq.sort_values("days_in_topk", ascending=False)

    freq.to_csv(a.out, index=False, encoding="utf-8-sig")
    print("[OK] wrote", a.out)
    print("n_days:", n_days, "total_picks:", total, "unique_panels_in_topk:", freq.shape[0])
    print(freq.head(20).to_string(index=False))

if __name__=="__main__":
    main()
