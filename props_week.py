from props import *
import json
d=json.load(open("week.json")); S,W=d["meta"]["season"],d["meta"]["week"]; w=SCH[(SCH.season==S)&(SCH.week==W)].copy()
inj=pd.read_parquet("inj.parquet"); out_ids=set(inj[(inj.season==S)&(inj.week==W)&inj.report_status.isin(["Out","Doubtful"])].gsis_id.dropna()); allp=set(PS[PS.season==S].player_id)-out_ids
marg={g["id"]:g["line"]["spread"]+g["model"]["c_spread"]+g["model"]["b_spread"]*g["line"]["spread"] for g in d["games"]}
pr,ctx=project(S,W,w,active=allp,margin=marg); T,D,DP=ctx["T"],ctx["D"],ctx["DP"]; r1=lambda x: None if pd.isna(x) else round(float(x),1)
for g in d["games"]:
    H,A=g["home"]["team"],g["away"]["team"]; teams={}
    for t,o in [(H,A),(A,H)]:
        mm=marg[g["id"]]*(1 if t==H else -1)
        teams[t]={"f_pass":round(float(D.f_pass.get(o,1)),3),"f_rush":round(float(D.f_rush.get(o,1)),3),"f_pos":{p:round(float(DP.get((o,p),1)),3) for p in ["WR","TE","RB"]},"proj_pass_att":r1(max(T.pa[t]-0.45*mm,20)),"proj_rush_att":r1(max(T.ru[t]+0.45*mm,15))}
    pp=pr[pr.game_id==g["id"]].copy(); pp=pp[(pp.pos=="QB")|(pp.rush_att.fillna(0)>=4)|(pp.targets.fillna(0)>=3)]
    pp["sk"]=pp.pos.map({"QB":0,"RB":1,"WR":2,"TE":3}).fillna(4)*-1000+pp.targets.fillna(0)+pp.rush_att.fillna(0); pls=[]
    for r in pp.sort_values(["team","sk"],ascending=[True,False]).itertuples():
        o={"name":r.name,"pos":r.pos,"team":r.team,"opp":r.opp,"g":int(r.g)}
        for k in ["pass_att","comp","pass_yds","pass_td","rush_att","rush_yds","targets","rec","rec_yds","rtd","retd"]:
            v=getattr(r,k,None)
            if v is not None and not pd.isna(v): o[k]=round(float(v),2)
        o["td_lambda"]=round(float(r.td_lambda),3); pls.append(o)
    g["props"]={"teams":teams,"players":pls}
json.dump(d,open("week.json","w"),ensure_ascii=False); print("props_week ok")
