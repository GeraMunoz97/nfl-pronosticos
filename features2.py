import pandas as pd, numpy as np, json
MAP={"SD":"LAC","STL":"LA","OAK":"LV"}; fix=lambda s:s.replace(MAP)
sch=pd.read_parquet("sched.parquet"); sch=sch[sch.season>=2012].copy(); order=sch[["game_id","gameday","season","week","game_type"]]
q=pd.read_parquet("qb_plays.parquet").dropna(subset=["id","qb_epa"])
qg=q.groupby(["game_id","id"]).agg(s=("qb_epa","sum"),n=("qb_epa","size")).reset_index().merge(order,on="game_id").sort_values(["id","gameday"])
C=json.load(open("qb_prior.json")); DR=pd.read_parquet("players_draft.parquet").set_index("gsis_id")
def prior_of(qid):
    pk=DR.draft_pick.get(qid) if qid in DR.index else None
    pk=300 if pk is None or pd.isna(pk) else min(float(pk),300); return C["0"]+C["1"]*np.log(pk)
rows=[]
for qid,d in qg.groupby("id"):
    S=N=0.0; PR=prior_of(qid)
    for gid,s,n in zip(d.game_id,d.s,d.n): rows.append((gid,qid,(S+200*PR)/(N+200),N)); S=S*0.9985**n+s; N=N*0.9985**n+n
pd.DataFrame(rows,columns=["game_id","qb_id","qb_rating","qb_exp"]).to_parquet("qb_ratings.parquet")
sn=pd.read_parquet("snaps.parquet").merge(pd.read_parquet("players.parquet").dropna(),left_on="pfr_player_id",right_on="pfr_id"); sn["team"]=fix(sn.team)
sn=sn.merge(order[["game_id","gameday"]],on="game_id").sort_values(["gsis_id","gameday"])
imp=sn.groupby(["gsis_id","season"]).apply(lambda d:d.assign(io=d.offense_pct.rolling(4,min_periods=1).mean(),idf=d.defense_pct.rolling(4,min_periods=1).mean())[["week","io","idf"]],include_groups=False).reset_index().drop(columns="level_2")
inj=pd.read_parquet("inj.parquet"); inj["team"]=fix(inj.team)
inj=inj[inj.report_status.isin(["Out","Doubtful","Questionable"])&(inj.position!="QB")].dropna(subset=["week","gsis_id"]).copy()
inj["prob_out"]=inj.report_status.map({"Out":1,"Doubtful":0.9,"Questionable":0.25})
for d_ in (inj,imp): d_["week"]=d_["week"].astype("int64"); d_["season"]=d_["season"].astype("int64")
inj=pd.merge_asof(inj.sort_values("week"),imp.sort_values("week"),on="week",by=["gsis_id","season"],allow_exact_matches=False); inj[["io","idf"]]=inj[["io","idf"]].fillna(0)
POSW={"T":1.0,"G":0.8,"C":0.8,"WR":1.0,"TE":0.7,"RB":0.5,"FB":0.2}
inj["w_off"]=inj.prob_out*inj.io*inj.position.map(POSW).fillna(0.3); inj["w_def"]=inj.prob_out*inj.idf
inj.groupby(["season","week","team"])[["w_off","w_def"]].sum().reset_index().to_parquet("inj_team.parquet"); print("features2 ok")
