import pandas as pd, json, os
d=json.load(open("week.json")); S,W=d["meta"]["season"],d["meta"]["week"]
inj=pd.read_parquet("inj.parquet"); inj=inj[(inj.season==S)&(inj.week==W)&inj.report_status.isin(["Out","Doubtful"])].copy()
sn=pd.read_parquet("snaps.parquet"); sn=sn[sn.season==S].merge(pd.read_parquet("players.parquet").dropna(),left_on="pfr_player_id",right_on="pfr_id"); inj["d"]=inj.gsis_id.map(sn.groupby("gsis_id").defense_pct.mean()).fillna(0)
SEC={"CB","S","FS","SS","DB"}; FR={"DE","DT","LB","OLB","ILB","MLB","NT","DL","EDGE"}
WN=json.load(open("state/wind.json")) if os.path.exists("state/wind.json") else {}; RF=json.load(open("state/roof.json")) if os.path.exists("state/roof.json") else {}
for g in d["games"]:
    if g["id"] in RF: g["roof"]=RF[g["id"]]
    if g["id"] in WN and g["roof"] not in ("dome","closed"): g["wind"]=WN[g["id"]]
    for t in [g["home"]["team"],g["away"]["team"]]:
        o=g["away"]["team"] if t==g["home"]["team"] else g["home"]["team"]; oi=inj[inj.team==o]; T=g["props"]["teams"][t]
        T["sec_out"]=round(float(oi[oi.position.isin(SEC)].d.sum()),2); T["fr_out"]=round(float(oi[oi.position.isin(FR)].d.sum()),2)
        T["sec_names"]=oi[oi.position.isin(SEC)&(oi.d>0.3)].full_name.tolist(); T["fr_names"]=oi[oi.position.isin(FR)&(oi.d>0.3)].full_name.tolist(); T["home"]=t==g["home"]["team"]
m=d["meta"]; m["factors"]={"sec":0.04,"home":0.015,"indoor":0.015,"wind_pass":-0.18,"front":0.025,"wind_rush":0.06,"wind_th":15}
m["props_cal"]=json.load(open("state/props_cal.json")); m["margin_table"]=json.load(open("state/margin_table.json")); m["tot_cal"]={"k":0.63,"star":0.56,"star_under":0.56,"star_over":0.526}
m["corr"]=json.load(open("state/corr.json")); m["calib"]=json.load(open("state/calib.json")) if os.path.exists("state/calib.json") else None
m["props_bt"]={"pass_yds":"60.7 vs 66.5","rush_yds":"20.2 vs 21.1","rec_yds":"17.6 vs 17.8","td":"calibradas en 2025"}; m["updated"]=pd.Timestamp.now(tz="America/Monterrey").strftime("%d/%m %H:%M")
json.dump(d,open("week.json","w"),ensure_ascii=False); print("update_factors ok",m["updated"])
