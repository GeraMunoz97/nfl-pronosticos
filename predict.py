from modelo2 import *
import json
_c=g[g.result.isna()&g.spread_line.notna()].sort_values("gameday")
SEASON, WEEK = (int(_c.iloc[0].season), int(_c.iloc[0].week)) if len(_c) else (int(g.season.max()), int(g[g.season==g.season.max()].week.max()))
print("Temporada",SEASON,"semana",WEEK)
done=g.result.notna()&g.spread_line.notna(); wk=(g.season==SEASON)&(g.week==WEEK); out={}
for tgt in ["result","total"]: out["pure_"+tgt]=fit_pred(done,wk,cols(tgt,"qi"),tgt)
for tgt,line in [("result","spread_line"),("total","total_line")]:
    Xr=X.copy(); Xr["mkt"]=g[line]; cs=cols(tgt,"qi")+["mkt"]
    rid=RidgeCV(alphas=np.logspace(0,4,20)).fit(Xr.loc[done,cs],(g[tgt]-g[line])[done]); out["c_"+tgt]=rid.intercept_+Xr.loc[wk,cs[:-1]].values@rid.coef_[:-1]; out["b_"+tgt]=rid.coef_[-1]
w=g[wk].copy()
allr=pd.concat([w[["home_team","h_r_off_epa","h_r_def_epa"]].set_axis(["t","o","d"],axis=1),w[["away_team","a_r_off_epa","a_r_def_epa"]].set_axis(["t","o","d"],axis=1)]).drop_duplicates("t").set_index("t")
rk_o=allr.o.rank(ascending=False).astype(int); rk_d=allr.d.rank().astype(int)
def tier(q): return "élite" if q>0.12 else "muy bueno" if q>0.07 else "promedio" if q>0.02 else "por debajo del promedio" if q>-0.04 else "débil / sin experiencia"
am=lambda v,d=-110: int(v) if pd.notna(v) else d; games=[]
for k,(i,r) in enumerate(w.iterrows()):
    def side(s,t):
        qbr=r[f"{s}_qbr"]; hab=r[f"{s}_qbhab"]; hab=qbr if pd.isna(hab) else hab
        return {"team":t,"qb":r[f"{s}_qb_name"],"qb_tier":tier(qbr),"qb_change":round(float(qbr-hab),3),"qb_exp_low":bool((r[f"{s}_qbx"] or 0)<150),"off_rank":int(rk_o[t]),"def_rank":int(rk_d[t]),"rest":int(r[f"{s}_rest"]),"injuries":[]}
    _k=pd.Timestamp(f"{r.gameday} {r.gametime}").tz_localize("America/New_York").tz_convert("America/Monterrey")
    games.append({"id":r.game_id,"date":str(r.gameday),"time":r.gametime,"mty":_k.strftime("%H:%M"),"mty_date":_k.strftime("%Y-%m-%d"),"home":side("home",r.home_team),"away":side("away",r.away_team),
      "roof":r.roof if isinstance(r.roof,str) else "desconocido","div":bool(r.div_game),"neutral":r.location=="Neutral",
      "line":{"spread":float(r.spread_line),"total":float(r.total_line),"ml_home":am(r.home_moneyline),"ml_away":am(r.away_moneyline),"spread_odds_home":am(r.home_spread_odds),"spread_odds_away":am(r.away_spread_odds),"over_odds":am(r.over_odds),"under_odds":am(r.under_odds)},
      "model":{"pure_margin":round(float(out["pure_result"][k]),2),"pure_total":round(float(out["pure_total"][k]),2),"c_spread":round(float(out["c_result"][k]),4),"b_spread":round(float(out["b_result"]),5),"c_total":round(float(out["c_total"][k]),4),"b_total":round(float(out["b_total"]),5)}})
meta={"season":SEASON,"week":WEEK,"sd_margin":12.9,"sd_total":13.3,"backtest":{"total":"unders ★ 108-80 (57.4%)","spread":"sin ventaja general","ml":"◆ en prueba"}}
json.dump({"meta":meta,"games":games},open("week.json","w"),ensure_ascii=False)
for x in games:
    L=x["line"]; m=x["model"]; tot=L["total"]+m["c_total"]+m["b_total"]*L["total"]
    print(f'{x["away"]["team"]:>3} @ {x["home"]["team"]:<3} {x["date"]} {x["mty"]} | sp {L["spread"]:+5.1f} tot {L["total"]:4.1f} | modelo tot {tot:5.1f} ({tot-L["total"]:+.2f}) | QB {x["away"]["qb"]} / {x["home"]["qb"]}')
print("QB_SWAP",QB_SWAP)
