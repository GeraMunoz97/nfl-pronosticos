import json, math
from guard import started
d=json.load(open("week.json")); H={x["id"] for x in json.load(open("history.json"))}; log=json.load(open("state/log.json")); S,W=d["meta"]["season"],d["meta"]["week"]
MT=json.load(open("state/margin_table.json")); cal=json.load(open("state/props_cal.json"))["td_cal"]; am=lambda a:(1+a/100) if a>0 else (1+100/abs(a))
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
fixed=lambda x: x.get("mk")=="td" or x["id"] in H or x["w"]!=W or started(x["id"])
keep=[x for x in log if fixed(x)]; kk={(x["id"],x.get("mk")) for x in keep}; new=[]; tds=[]
for g in d["games"]:
    if g["id"] in H or started(g["id"]): continue
    L=g["line"]; m=g["model"]; tl=L["total"]; sl=L["spread"]; tot=tl+m["c_total"]+m["b_total"]*tl; mar=sl+m["c_spread"]+m["b_spread"]*sl
    base={"s":S,"w":W,"id":g["id"],"a":g["away"]["team"],"h":g["home"]["team"],"date":d["meta"].get("updated","")}; diff=tot-tl
    if abs(diff)>=1 and (g["id"],"total") not in kk:
        over=diff>0; o=am(L["over_odds"] if over else L["under_odds"]); pp=0.526 if over else 0.56
        if pp*(o-1)-(1-pp)>0: new.append({**base,"mk":"total","tier":"dia" if over else "star","side":"over" if over else "under","line":tl,"odds":round(o,2),"proj":round(tot,1)})
    ph=pgt(mar,sl)/max(1e-9,1-peq(mar,sl)); home=ph>=0.5; p=max(ph,1-ph); o=am(L["spread_odds_home"] if home else L["spread_odds_away"])
    if p>=0.56 and p*o-1>0 and (g["id"],"spread") not in kk: new.append({**base,"mk":"spread","team":g["home"]["team"] if home else g["away"]["team"],"line":-sl if home else sl,"odds":round(o,2),"p":round(p,3)})
    pw=pgt(mar,0)+0.5*peq(mar,0); oh,oa=am(L["ml_home"]),am(L["ml_away"]); pm=(1/oh)/((1/oh)+(1/oa))
    for pp,pmk,oo,t in [(pw,pm,oh,g["home"]["team"]),(1-pw,1-pm,oa,g["away"]["team"])]:
        if pp-pmk>=0.05 and (g["id"],"ml") not in kk: new.append({**base,"mk":"ml","team":t,"odds":round(oo,2),"p":round(pp,3),"pm":round(pmk,3)})
    for p_ in g["props"]["players"]:
        if p_["pos"]!="QB": tds.append({**base,"mk":"td","player":p_["name"],"team":p_["team"],"p":round(tdp(p_["td_lambda"]),3)})
if not any(x.get("mk")=="td" and x["w"]==W for x in keep): new+=sorted(tds,key=lambda x:-x["p"])[:5]
json.dump(keep+new,open("state/log.json","w"),ensure_ascii=False)
print("log S%d:"%W,[(x["mk"],x.get("tier",""),x["a"]+"@"+x["h"],x.get("side",x.get("team",x.get("player"))),x.get("line",""),x.get("odds","")) for x in keep+new if x["w"]==W])
