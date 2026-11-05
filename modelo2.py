import pandas as pd, numpy as np, json, os
from sklearn.linear_model import RidgeCV
import lightgbm as lgb
MAP={"SD":"LAC","STL":"LA","OAK":"LV"}
g=pd.read_parquet("sched.parquet"); g=g[g.season>=2012].copy().reset_index(drop=True)
for c in ["home_team","away_team"]: g[c]=g[c].replace(MAP)
r=pd.read_parquet("team_ratings.parquet"); rc=[c for c in r.columns if c.startswith("r_")]
g=g.merge(r.add_prefix("h_").rename(columns={"h_game_id":"game_id","h_team":"home_team"}),on=["game_id","home_team"],how="left").merge(r.add_prefix("a_").rename(columns={"a_game_id":"game_id","a_team":"away_team"}),on=["game_id","away_team"],how="left")
_inj=pd.read_parquet("inj.parquet"); _o=_inj[_inj.report_status.isin(["Out","Doubtful"])&(_inj.position=="QB")]; OUT=set(zip(_o.season,_o.week,_o.gsis_id))
_h=pd.concat([g[g.result.notna()][["gameday","home_team","home_qb_id","home_qb_name"]].set_axis(["d","t","id","n"],axis=1),g[g.result.notna()][["gameday","away_team","away_qb_id","away_qb_name"]].set_axis(["d","t","id","n"],axis=1)]).sort_values("d")
QB_SWAP=[]
for s in ["home","away"]:
    for ix in g.index[g.result.isna()]:
        rr=g.loc[ix]; qid=rr[f"{s}_qb_id"]
        if (rr.season,rr.week,qid) in OUT:
            pv=_h[(_h.t==rr[f"{s}_team"])&(_h.d<rr.gameday)&(_h.id!=qid)]; pv=pv[[(rr.season,rr.week,z) not in OUT for z in pv.id]]
            if len(pv): g.at[ix,f"{s}_qb_id"]=pv.iloc[-1].id; g.at[ix,f"{s}_qb_name"]=pv.iloc[-1].n; QB_SWAP.append((rr.game_id,qid,pv.iloc[-1].n))
qr=pd.read_parquet("qb_ratings.parquet"); C=json.load(open("qb_prior.json")); DR=pd.read_parquet("players_draft.parquet").set_index("gsis_id")
def prior_of(qid):
    pk=DR.draft_pick.get(qid) if qid in DR.index else None
    pk=300 if pk is None or pd.isna(pk) else min(float(pk),300); return C["0"]+C["1"]*np.log(pk)
for s in ["home","away"]: g=g.merge(qr.rename(columns={"qb_id":f"{s}_qb_id","qb_rating":f"{s}_qbr","qb_exp":f"{s}_qbx"}),on=["game_id",f"{s}_qb_id"],how="left")
q=pd.read_parquet("qb_plays.parquet").dropna(subset=["id","qb_epa"]); q=q.groupby(["game_id","id"]).agg(s=("qb_epa","sum"),n=("qb_epa","size")).reset_index().merge(g[["game_id","gameday"]],on="game_id").sort_values("gameday"); cur={}
for qid,d in q.groupby("id"):
    S=N=0.0
    for s_,n_ in zip(d.s,d.n): S=S*0.9985**n_+s_; N=N*0.9985**n_+n_
    cur[qid]=((S+200*prior_of(qid))/(N+200),N)
for s in ["home","away"]:
    m=g.result.isna()&g[f"{s}_qb_id"].notna()
    g.loc[m,f"{s}_qbr"]=g.loc[m,f"{s}_qb_id"].map(lambda i:cur.get(i,(prior_of(i),0))[0]); g.loc[m,f"{s}_qbx"]=g.loc[m,f"{s}_qb_id"].map(lambda i:cur.get(i,(0,0))[1]); g[f"{s}_qbr"]=g[f"{s}_qbr"].fillna(-0.08)
tq=pd.concat([g[["game_id","gameday","home_team","home_qbr"]].set_axis(["game_id","gameday","team","qbr"],axis=1),g[["game_id","gameday","away_team","away_qbr"]].set_axis(["game_id","gameday","team","qbr"],axis=1)]).sort_values("gameday")
tq["qb_hab"]=tq.groupby("team").qbr.transform(lambda x:x.shift(1).ewm(halflife=6).mean())
for s in ["home","away"]: g=g.merge(tq[["game_id","team","qb_hab"]].rename(columns={"team":f"{s}_team","qb_hab":f"{s}_qbhab"}),on=["game_id",f"{s}_team"],how="left")
it=pd.read_parquet("inj_team.parquet")
for s in ["home","away"]:
    g=g.merge(it.rename(columns={"team":f"{s}_team","w_off":f"{s}_injo","w_def":f"{s}_injd"}),on=["season","week",f"{s}_team"],how="left"); g[[f"{s}_injo",f"{s}_injd"]]=g[[f"{s}_injo",f"{s}_injd"]].fillna(0)
if os.path.exists("state/roof.json"):
    RF=json.load(open("state/roof.json")); mm=g.game_id.isin(RF.keys()); g.loc[mm,"roof"]=g.loc[mm,"game_id"].map(RF)
if os.path.exists("state/wind.json"):
    W=json.load(open("state/wind.json")); m=g.result.isna()&g.game_id.isin(W.keys()); g.loc[m,"wind"]=g.loc[m,"game_id"].map(W)
X=pd.DataFrame(index=g.index)
for c in rc: X["d_"+c]=g["h_"+c]-g["a_"+c]; X["s_"+c]=g["h_"+c]+g["a_"+c]
X["b_rest"]=(g.home_rest-g.away_rest).clip(-7,7); X["b_neutral"]=(g.location=="Neutral").astype(int); X["b_div"]=g.div_game; X["b_indoor"]=g.roof.isin(["dome","closed"]).astype(int)
X["b_wind"]=np.where(X.b_indoor==1,0,g.wind.fillna(8)); X["b_temp"]=np.where(X.b_indoor==1,70,g.temp.fillna(60)); X["b_playoff"]=(g.game_type!="REG").astype(int)
X["q_d_qbr"]=g.home_qbr-g.away_qbr; X["q_s_qbr"]=g.home_qbr+g.away_qbr; X["q_d_chg"]=(g.home_qbr-g.home_qbhab)-(g.away_qbr-g.away_qbhab); X["q_s_chg"]=(g.home_qbr-g.home_qbhab)+(g.away_qbr-g.away_qbhab)
X["i_d_off"]=g.home_injo-g.away_injo; X["i_d_def"]=g.home_injd-g.away_injd; X["i_s_off"]=g.home_injo+g.away_injo; X["i_s_def"]=g.home_injd+g.away_injd
X=X.fillna(X.mean())
def cols(tgt,grp):
    keep="d_" if tgt=="result" else "s_"; return [c for c in X if (c.startswith("b_") or c.startswith(keep) or (c[0] in grp and c[2:4]==keep))]
def fit_pred(tr,te,cs,tgt):
    rid=RidgeCV(alphas=np.logspace(-2,3,20)).fit(X.loc[tr,cs],g.loc[tr,tgt])
    gb=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.02,num_leaves=8,min_child_samples=60,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,verbose=-1).fit(X.loc[tr,cs],g.loc[tr,tgt])
    return 0.5*rid.predict(X.loc[te,cs])+0.5*gb.predict(X.loc[te,cs])
