import pandas as pd, numpy as np, json
from props import PS
d=json.load(open("week.json")); S,W=d["meta"]["season"],d["meta"]["week"]; h=PS[(PS.season==S)&(PS.week<W)].copy(); h["td"]=h.rushing_tds.fillna(0)+h.receiving_tds.fillna(0)
ag=h.groupby("player_id").agg(g=("week","nunique"),att=("attempts","sum"),pyd=("passing_yards","sum"),ptd=("passing_tds","sum"),car=("carries","sum"),ryd=("rushing_yards","sum"),tgt=("targets","sum"),rec=("receptions","sum"),yds=("receiving_yards","sum"),td=("td","sum"))
avg=ag.drop(columns="g").div(ag.g,axis=0).round(1); avg["g"]=ag.g; nm=h.drop_duplicates(["player_display_name","team"],keep="last").set_index(["player_display_name","team"])["player_id"]; ng=h.groupby("opponent_team").week.nunique()
cols={"QB":["attempts","passing_yards","passing_tds","rushing_yards"],"RB":["carries","rushing_yards","receptions","receiving_yards","td"],"WR":["targets","receptions","receiving_yards","td"],"TE":["targets","receptions","receiving_yards","td"]}
DEF={p:{c:h[h.position==p].groupby("opponent_team")[c].sum()/ng for c in cs} for p,cs in cols.items()}
for g in d["games"]:
    for p in g["props"]["players"]:
        pid=nm.get((p["name"],p["team"])); p["avg"]=avg.loc[pid].to_dict() if pid in avg.index else None
        if p["pos"] in DEF: p["oppd"]={c:[round(float(s.get(p["opp"],np.nan)),1),int(s.rank(method="min").get(p["opp"],0))] for c,s in DEF[p["pos"]].items()}
json.dump(d,open("week.json","w"),ensure_ascii=False); print("player_ctx ok")
