import polars as pl, pandas as pd, numpy as np
MAP={"SD":"LAC","STL":"LA","OAK":"LV"}
pbp=pl.read_parquet("pbp.parquet").with_columns(pl.col("posteam").replace(MAP),pl.col("defteam").replace(MAP))
sch=pl.read_parquet("sched.parquet").filter(pl.col("season")>=2012).to_pandas()
for c in ["home_team","away_team"]: sch[c]=sch[c].replace(MAP)
def agg(side,team):
    g=pbp.group_by(["game_id",side]).agg(pl.col("epa").mean().alias("epa"),pl.col("success").mean().alias("sr"),pl.col("epa").filter(pl.col("pass")==1).mean().alias("pass_epa"),pl.col("epa").filter(pl.col("rush")==1).mean().alias("rush_epa"),pl.len().alias("plays")).rename({side:"team"})
    return g.to_pandas().set_index(["game_id","team"]).add_prefix(team+"_")
tg=agg("posteam","off").join(agg("defteam","def"),how="outer").reset_index()
h=sch[["game_id","home_team","home_score","away_score"]].rename(columns={"home_team":"team","home_score":"pf","away_score":"pa"})
a=sch[["game_id","away_team","away_score","home_score"]].rename(columns={"away_team":"team","away_score":"pf","home_score":"pa"})
tg=tg.merge(pd.concat([h,a]),on=["game_id","team"],how="right").merge(sch[["game_id","season","week","gameday"]],on="game_id").sort_values(["team","gameday"])
stats=[c for c in tg.columns if c.startswith(("off_","def_"))]+["pf","pa"]; out=[]
for t,d in tg.groupby("team"):
    d=d.copy()
    for c in stats: d["r_"+c]=d[c].shift(1).ewm(halflife=8,ignore_na=True).mean()
    d["n_prev"]=d.groupby("season").cumcount(); out.append(d)
tg=pd.concat(out); rc=["r_"+c for c in stats]; mean=tg[rc].mean(); w=(tg.n_prev.clip(upper=6)/6*0.5+0.5).values[:,None]; tg[rc]=tg[rc].values*w+mean.values*(1-w)
tg[["game_id","team"]+rc].to_parquet("team_ratings.parquet"); print("features ok")
