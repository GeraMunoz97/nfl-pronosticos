import pandas as pd, numpy as np, json
q=pd.read_parquet("qb_plays.parquet").dropna(subset=["id","qb_epa"]).merge(pd.read_parquet("sched.parquet")[["game_id","gameday"]],on="game_id").sort_values(["id","gameday"])
q["n"]=q.groupby("id").cumcount(); f=q[q.n<250].groupby("id").agg(epa=("qb_epa","mean"),n=("qb_epa","size"))
d=pd.read_parquet("players_draft.parquet").set_index("gsis_id"); f=f.join(d,how="inner"); f=f[((f.draft_year>=2012)|f.draft_year.isna())&(f.n>=60)]
pk=f.draft_pick.fillna(300).clip(upper=300); X=np.vstack([np.ones(len(f)),np.log(pk)]).T; w=np.sqrt(f.n.values)
c=np.linalg.lstsq(X*w[:,None],f.epa.values*w,rcond=None)[0]; json.dump({"0":float(c[0]),"1":float(c[1])},open("qb_prior.json","w")); print("qbprior ok")
