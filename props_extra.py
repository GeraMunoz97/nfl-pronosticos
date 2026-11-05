from props import *
import json
d=json.load(open("week.json")); S,W=d["meta"]["season"],d["meta"]["week"]; h=PS[(PS.season==S)&(PS.week<W)]; ng=h.groupby("team").week.nunique(); ngo=h.groupby("opponent_team").week.nunique()
pg=lambda df,k,c,n: df.groupby(k)[c].sum()/n
st={"pass":(pg(h,"team","passing_yards",ng),pg(h,"opponent_team","passing_yards",ngo)),"rush":(pg(h,"team","rushing_yards",ng),pg(h,"opponent_team","rushing_yards",ngo)),"rec":(pg(h,"team","receptions",ng),pg(h,"opponent_team","receptions",ngo))}
for p in ["WR","TE","RB"]:
    hp=h[h.position==p]; st["yds_"+p]=(pg(hp,"team","receiving_yards",ng),pg(hp,"opponent_team","receiving_yards",ngo)); st["rec_"+p]=(pg(hp,"team","receptions",ng),pg(hp,"opponent_team","receptions",ngo))
s26=SCH[(SCH.season==S)&(SCH.week<W)&SCH.result.notna()]
st["pts"]=(pd.concat([s26[["home_team","home_score"]].set_axis(["t","v"],axis=1),s26[["away_team","away_score"]].set_axis(["t","v"],axis=1)]).groupby("t").v.mean(),
           pd.concat([s26[["home_team","away_score"]].set_axis(["t","v"],axis=1),s26[["away_team","home_score"]].set_axis(["t","v"],axis=1)]).groupby("t").v.mean())
def card(t,o):
    out={}
    for k,(of,df) in st.items(): ro=of.rank(ascending=False,method="min"); rd=df.rank(method="min"); out[k]=[round(float(of.get(t,np.nan)),1),int(ro.get(t,0)),round(float(df.get(o,np.nan)),1),int(rd.get(o,0))]
    return out
inj=pd.read_parquet("inj.parquet"); inj=inj[(inj.season==S)&(inj.week==W)].copy()
sn=pd.read_parquet("snaps.parquet"); sn=sn[sn.season==S].merge(pd.read_parquet("players.parquet").dropna(),left_on="pfr_player_id",right_on="pfr_id")
inj=inj.join(sn.groupby("gsis_id").agg(o=("offense_pct","mean"),de=("defense_pct","mean")),on="gsis_id"); inj[["o","de"]]=inj[["o","de"]].fillna(0); inj["imp"]=inj[["o","de"]].max(axis=1)
PR={"Did Not Participate In Practice":"No entrenó","Limited Participation in Practice":"Entrenó limitado","Full Participation in Practice":"Entrenó completo"}; RS={"Out":"Fuera","Doubtful":"Dudoso","Questionable":"En duda"}
w=SCH[(SCH.season==S)&(SCH.week==W)]; out_ids=set(inj[inj.report_status.isin(["Out","Doubtful"])].gsis_id.dropna()); base_active=set(PS[PS.season==S].player_id)-out_ids
marg={g["id"]:g["line"]["spread"]+g["model"]["c_spread"]+g["model"]["b_spread"]*g["line"]["spread"] for g in d["games"]}
def effect(pos):
    if pos in ("T","G","C","OL"): return "Línea ofensiva: menos protección para el QB y menos espacios para correr."
    if pos in ("CB","S","DB","FS","SS"): return "Secundaria: debilita la defensa contra el pase; favorece a los receptores rivales."
    if pos in ("DE","DT","LB","OLB","ILB","EDGE","DL","NT","MLB"): return "Defensa frontal: menos presión al QB y peor defensa contra la carrera."
    if pos=="QB": return "Quarterback: es la baja que más mueve la línea. Si no juega, el modelo usa al último titular sano del equipo."
    return ""
PSids=set(PS[PS.season==S].player_id)
for g in d["games"]:
    H,A=g["home"]["team"],g["away"]["team"]; gm=w[w.game_id==g["id"]]; g["props"]["cards"]={H:card(H,A),A:card(A,H)}
    base,_=project(S,W,gm,active=base_active,margin=marg); base=base.set_index("player_id"); lst=[]
    for r in inj[inj.team.isin([H,A])].sort_values("imp",ascending=False).itertuples():
        status=RS.get(r.report_status) or PR.get(r.practice_status)
        if status is None or status=="Entrenó completo" or (r.imp<0.35 and r.position!="QB"): continue
        e={"team":r.team,"name":r.full_name,"pos":r.position,"status":status,"injury":r.report_primary_injury if isinstance(r.report_primary_injury,str) else "","snaps":round(float(r.imp)*100),"effect":effect(r.position),"gains":[]}
        if r.position in ("WR","TE","RB") and r.gsis_id in PSids:
            if r.gsis_id in out_ids: alt,_=project(S,W,gm,active=base_active|{r.gsis_id},margin=marg); A_,B_=alt.set_index("player_id"),base; lead="Ya está descontado en las proyecciones."
            else: alt,_=project(S,W,gm,active=base_active-{r.gsis_id},margin=marg); A_,B_=base,alt.set_index("player_id"); lead="Las proyecciones asumen que juega."
            if r.gsis_id in A_.index:
                me=A_.loc[r.gsis_id]; vol=(me.get("targets") or 0)+(me.get("rush_att") or 0); diffs=[]
                for pid in B_.index.intersection(A_.index):
                    if pid==r.gsis_id: continue
                    dt=(B_.loc[pid].get("targets") or 0)-(A_.loc[pid].get("targets") or 0); dr=(B_.loc[pid].get("rush_att") or 0)-(A_.loc[pid].get("rush_att") or 0)
                    dy=(B_.loc[pid].get("rec_yds") or 0)+(B_.loc[pid].get("rush_yds") or 0)-(A_.loc[pid].get("rec_yds") or 0)-(A_.loc[pid].get("rush_yds") or 0)
                    if dt+dr>0.6: diffs.append((dt+dr,B_.loc[pid]["name"],dt,dr,dy))
                diffs.sort(reverse=True); e["effect"]=f"{lead} Si no juega, deja libres unos {vol:.1f} targets/acarreos por partido."; e["gains"]=[f"{n}: +{dt+dr:.1f} {'targets' if dt>=dr else 'acarreos'}, +{dy:.0f} yds" for _,n,dt,dr,dy in diffs[:3]]
        lst.append(e)
    lst.sort(key=lambda e:(e["pos"]!="QB",e["pos"] not in ("WR","TE","RB"),-e["snaps"])); g["injuries"]=lst[:10]
json.dump(d,open("week.json","w"),ensure_ascii=False); print("props_extra ok")
