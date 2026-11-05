import json, math
from guard import started
d=json.load(open("week.json")); H={x["id"] for x in json.load(open("history.json"))}; MT=json.load(open("state/margin_table.json")); cal=json.load(open("state/props_cal.json"))["td_cal"]; P=json.load(open("state/picks.json"))
def dist(m): return MT["t"][max(0,min(len(MT["t"])-1,round((m-MT["grid"][0])*2)))]
def pgt(m,L): return sum(v for k,v in enumerate(dist(m)) if MT["lo"]+k>L)
def peq(m,L):
    if float(L)!=int(L): return 0
    k=int(L)-MT["lo"]; h=dist(m); return h[k] if 0<=k<len(h) else 0
def tdp(l):
    p=1-math.exp(-l)
    if p<=cal[0][0]: return p*cal[0][1]/max(cal[0][0],1e-3)
    for i in range(len(cal)-1):
        if p<=cal[i+1][0]: f=(p-cal[i][0])/(cal[i+1][0]-cal[i][0]); return cal[i][1]+f*(cal[i+1][1]-cal[i][1])
    return min(.9,p*cal[-1][1]/cal[-1][0])
for g in d["games"]:
    if g["id"] in H or (g["id"] in P and started(g["id"])): continue
    L=g["line"]; m=g["model"]; sl=L["spread"]; tl=L["total"]; mar=sl+m["c_spread"]+m["b_spread"]*sl; tot=tl+m["c_total"]+m["b_total"]*tl
    ph=pgt(mar,sl)/max(1e-9,1-peq(mar,sl)); hs=-sl; home_sp=ph>=0.5; pw=pgt(mar,0)+0.5*peq(mar,0)
    tds=sorted([(p["name"],p["team"],tdp(p["td_lambda"])) for p in g["props"]["players"] if p["pos"]!="QB"],key=lambda x:-x[2])[:3]
    P[g["id"]]={"date":d["meta"].get("updated",""),"winner":g["home"]["team"] if mar>=0 else g["away"]["team"],"wp":round(max(pw,1-pw),3),"sp_team":g["home"]["team"] if home_sp else g["away"]["team"],"sp_line":hs if home_sp else -hs,"sp_p":round(max(ph,1-ph),3),
      "tot_side":"over" if tot>tl else "under","tot_line":tl,"tot_proj":round(tot,1),"sig":tot-tl<=-1,"dia_over":tot-tl>=1,"score":[round((tot-mar)/2),round((tot+mar)/2)],"td":[[n,t,round(p,3)] for n,t,p in tds]}
json.dump(P,open("state/picks.json","w"),ensure_ascii=False); print("snap ok",len(P))
