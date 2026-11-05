import pandas as pd, numpy as np
PS=pd.read_parquet("pstats.parquet"); PS=PS[PS.season_type=="REG"].copy(); SCH=pd.read_parquet("sched.parquet")
def rg(num,den,prior,k): return (num+prior*k)/(den+k)
def project(season,week,games,active=None,margin=None,prior=True):
    h=PS[(PS.season==season)&(PS.week<week)]
    tw=h.groupby(["team","week"]).agg(pa=("attempts","sum"),ru=("carries","sum")).reset_index(); T=tw.groupby("team").agg(pa=("pa","mean"),ru=("ru","mean"),n=("week","nunique"))
    T["pa"]=rg(T.pa*T.n,T.n,tw.pa.mean(),3); T["ru"]=rg(T.ru*T.n,T.n,tw.ru.mean(),3)
    lg=dict(ypa=h.passing_yards.sum()/h.attempts.sum(),ptd=h.passing_tds.sum()/h.attempts.sum(),ypc=h.rushing_yards.sum()/h.carries.sum(),rtd=h.rushing_tds.sum()/h.carries.sum())
    D=h.groupby("opponent_team").agg(pyd=("passing_yards","sum"),pat=("attempts","sum"),ptd=("passing_tds","sum"),ryd=("rushing_yards","sum"),car=("carries","sum"),rtd=("rushing_tds","sum"))
    D["f_pass"]=rg(D.pyd,D.pat,lg["ypa"],150)/lg["ypa"]; D["f_ptd"]=rg(D.ptd,D.pat,lg["ptd"],300)/lg["ptd"]; D["f_rush"]=rg(D.ryd,D.car,lg["ypc"],100)/lg["ypc"]; D["f_rtd"]=rg(D.rtd,D.car,lg["rtd"],200)/lg["rtd"]
    rp=h[h.position.isin(["WR","TE","RB"])]; lp=rp.groupby("position").agg(t=("targets","sum"),y=("receiving_yards","sum")); lp["ypt"]=lp.y/lp.t
    DP=rp.groupby(["opponent_team","position"]).agg(t=("targets","sum"),y=("receiving_yards","sum")).reset_index(); DP["f"]=DP.apply(lambda r:rg(r.y,r.t,lp.ypt[r.position],50)/lp.ypt[r.position],axis=1); DPf=DP.set_index(["opponent_team","position"]).f
    tg=h.merge(tw[["team","week","pa","ru"]].rename(columns={"pa":"tpa","ru":"tru"}),on=["team","week"])
    P=tg.groupby(["player_id","player_display_name","position","team"]).agg(g=("week","nunique"),att=("attempts","sum"),pyd=("passing_yards","sum"),ptd=("passing_tds","sum"),cmp=("completions","sum"),car=("carries","sum"),ryd=("rushing_yards","sum"),rtd=("rushing_tds","sum"),tgt=("targets","sum"),rec=("receptions","sum"),yds=("receiving_yards","sum"),retd=("receiving_tds","sum"),tpa=("tpa","sum"),tru=("tru","sum")).reset_index()
    P=P.sort_values("g").drop_duplicates("player_id",keep="last")
    prv=PS[PS.season==season-1].groupby(["player_id","team"]).agg(ptg=("targets","sum"),pca=("carries","sum")).reset_index(); ptm=PS[PS.season==season-1].groupby(["team","week"]).agg(pa=("attempts","sum"),ru=("carries","sum")).groupby("team").sum()
    prv=prv.join(ptm,on="team"); prv["psh_t"]=prv.ptg/prv.pa.clip(lower=1); prv["psh_c"]=prv.pca/prv.ru.clip(lower=1); prv=prv.set_index(["player_id","team"])
    pos_lg=h.groupby("position")[["carries","rushing_yards","rushing_tds","targets","receptions","receiving_yards","receiving_tds"]].sum(); out=[]
    for gm in games.itertuples():
        for side,team,opp in [("home",gm.home_team,gm.away_team),("away",gm.away_team,gm.home_team)]:
            if team not in T.index: continue
            m=(margin or {}).get(gm.game_id,0.0)*(1 if side=="home" else -1); tpa=max(T.pa[team]-0.45*m,20); tru=max(T.ru[team]+0.45*m,15)
            pl=P[P.team==team].copy()
            if active is not None: pl=pl[pl.player_id.isin(active)]
            pl["sh_t"]=pl.tgt/pl.tpa.clip(lower=1); pl["sh_c"]=pl.car/pl.tru.clip(lower=1)
            if prior:
                for ix,rr in pl.iterrows():
                    if (rr.player_id,team) in prv.index and rr.g<6:
                        pv=prv.loc[(rr.player_id,team)]; kk=3.0*(1-rr.g/6); pl.at[ix,"sh_t"]=(rr.sh_t*rr.g+pv.psh_t*kk)/(rr.g+kk); pl.at[ix,"sh_c"]=(rr.sh_c*rr.g+pv.psh_c*kk)/(rr.g+kk)
            qbs=pl[pl.position=="QB"].sort_values("att",ascending=False); qid=getattr(gm,f"{side}_qb_id",None)
            qb=qbs[qbs.player_id==qid].iloc[0] if qid in set(qbs.player_id) else (qbs.iloc[0] if len(qbs) else None)
            st=pl.sh_t.where(pl.position!="QB",0).sum(); sc=pl.sh_c.sum()
            if qb is not None: sc=sc-pl.loc[pl.position=="QB","sh_c"].sum()+qb.car/max(qb.tru,1)
            fp=D.f_pass.get(opp,1); fr=D.f_rush.get(opp,1); fpt=D.f_ptd.get(opp,1); frt=D.f_rtd.get(opp,1)
            for r in pl.itertuples():
                if r.position=="QB" and (qb is None or r.player_id!=qb.player_id): continue
                o={"game_id":gm.game_id,"player_id":r.player_id,"name":r.player_display_name,"pos":r.position,"team":team,"opp":opp,"g":r.g}
                if r.position=="QB":
                    o["pass_att"]=tpa*0.97; o["pass_yds"]=o["pass_att"]*rg(r.pyd,r.att,lg["ypa"],120)*fp; o["pass_td"]=o["pass_att"]*rg(r.ptd,r.att,lg["ptd"],200)*fpt; o["comp"]=o["pass_att"]*rg(r.cmp,r.att,0.65,120)
                o["rush_att"]=(r.sh_c/sc if sc>0 else 0)*0.98*tru; pr=pos_lg.loc[r.position] if r.position in pos_lg.index else pos_lg.sum()
                o["rush_yds"]=o["rush_att"]*rg(r.ryd,r.car,pr.rushing_yards/max(pr.carries,1),40)*fr; rtd=o["rush_att"]*rg(r.rtd,r.car,pr.rushing_tds/max(pr.carries,1),60)*frt; retd=0
                if r.position!="QB":
                    o["targets"]=(r.sh_t/st if st>0 else 0)*0.93*tpa; o["rec"]=o["targets"]*rg(r.rec,r.tgt,pr.receptions/max(pr.targets,1),30)
                    o["rec_yds"]=o["targets"]*rg(r.yds,r.tgt,pr.receiving_yards/max(pr.targets,1),30)*DPf.get((opp,r.position),1); retd=o["targets"]*rg(r.retd,r.tgt,pr.receiving_tds/max(pr.targets,1),60)*fpt
                o["td_lambda"]=rtd+retd; o["rtd"]=rtd; o["retd"]=retd; g_=max(r.g,1)
                W={"pass_att":.7,"pass_yds":.7,"comp":.7,"rush_att":.7,"rush_yds":.7,"targets":.5,"rec":.5,"rec_yds":.5}
                nv={"pass_att":r.att/g_,"pass_yds":r.pyd/g_,"comp":r.cmp/g_,"rush_att":r.car/g_,"rush_yds":r.ryd/g_,"targets":r.tgt/g_,"rec":r.rec/g_,"rec_yds":r.yds/g_}
                for k_,w_ in W.items():
                    if k_ in o: o[k_]=w_*o[k_]+(1-w_)*nv[k_]
                out.append(o)
    return pd.DataFrame(out),{"T":T,"D":D,"DP":DPf}
