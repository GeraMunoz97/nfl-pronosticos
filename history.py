from modelo2 import *
import json, math, warnings; warnings.filterwarnings("ignore")
rows=[]
for S in [2021,2022,2023,2024,2025,2026]:
    te=(g.season==S)&g.result.notna()&g.spread_line.notna(); pr={}
    for tgt,line in [("result","spread_line"),("total","total_line")]:
        Xr=X.copy(); Xr["mkt"]=g[line]; cs=cols(tgt,"qi")+["mkt"]; tr=(g.season<S)&g.result.notna()&g[line].notna()
        rid=RidgeCV(alphas=np.logspace(0,4,20)).fit(Xr.loc[tr,cs],(g[tgt]-g[line])[tr]); pr[tgt]=g.loc[te,line].values+rid.predict(Xr.loc[te,cs])
    d=g.loc[te,["game_id","season","week","game_type","home_team","away_team","home_score","away_score","spread_line","total_line"]].copy(); d["m"]=pr["result"]; d["t"]=pr["total"]; rows.append(d)
H=pd.concat(rows)
from props import project, PS, SCH
cal=json.load(open("state/props_cal.json"))["td_cal"]
def tdp(l):
    p=1-math.exp(-l)
    if p<=cal[0][0]: return p*cal[0][1]/max(cal[0][0],1e-3)
    for i in range(len(cal)-1):
        if p<=cal[i+1][0]: f=(p-cal[i][0])/(cal[i+1][0]-cal[i][0]); return cal[i][1]+f*(cal[i+1][1]-cal[i][1])
    return min(.9,p*cal[-1][1]/cal[-1][0])
td={}; SC={}
for S in sorted(H.season.unique()):
    for wk in sorted(H[H.season==S].week.unique()):
        gms=SCH[(SCH.season==S)&(SCH.week==wk)].copy(); gms["home_team"]=gms.home_team.replace({"OAK":"LV"}); gms["away_team"]=gms.away_team.replace({"OAK":"LV"})
        real=PS[(PS.season==S)&(PS.week==wk)]
        if real.empty: continue
        for gid_,gm_ in gms.groupby("game_id"): SC[gid_]=real[((real.rushing_tds+real.receiving_tds)>0)&real.team.isin({gm_.home_team.iloc[0],gm_.away_team.iloc[0]})].player_display_name.tolist()
        if wk<2: continue
        act=set(real.player_id); scored=set(real[(real.rushing_tds+real.receiving_tds)>0].player_id)
        p,_=project(S,wk,gms,active=act,margin=dict(zip(gms.game_id,gms.spread_line)))
        if p.empty: continue
        p=p[p.pos!="QB"].copy(); p["tp"]=p.td_lambda.map(tdp)
        for gid,gp in p.groupby("game_id"): td[gid]=[[r.name,r.team,round(r.tp,3),int(r.player_id in scored)] for r in gp.sort_values("tp",ascending=False).head(3).itertuples()]
out=[{"id":r.game_id,"s":int(r.season),"w":int(r.week),"po":r.game_type!="REG","h":r.home_team,"a":r.away_team,"hs":int(r.home_score),"as":int(r.away_score),"sl":float(r.spread_line),"tl":float(r.total_line),"m":round(float(r.m),2),"t":round(float(r.t),2),"td":td.get(r.game_id,[]),"sc":SC.get(r.game_id,[])} for r in H.itertuples()]
json.dump(out,open("history.json","w"),ensure_ascii=False,separators=(",",":")); print("history ok",len(out))
