import nflreadpy as nfl, polars as pl, gc
cols=["game_id","season","week","posteam","defteam","play_type","epa","success","pass","rush","qb_dropback"]; parts=[];qp=[]
for y in range(2012,2027):
    p=nfl.load_pbp([y])
    parts.append(p.select([c for c in cols if c in p.columns]).filter(pl.col("play_type").is_in(["pass","run"])&pl.col("epa").is_not_null()))
    qp.append(p.filter(pl.col("qb_dropback")==1).select(["game_id","season","week","posteam","id","name","qb_epa"])); del p; gc.collect()
pl.concat(parts).write_parquet("pbp.parquet"); pl.concat(qp).write_parquet("qb_plays.parquet")
nfl.load_schedules().write_parquet("sched.parquet"); yrs=list(range(2012,2027))
nfl.load_injuries(yrs).write_parquet("inj.parquet"); nfl.load_snap_counts(yrs).write_parquet("snaps.parquet")
P=nfl.load_players(); P.select(["gsis_id","pfr_id"]).write_parquet("players.parquet")
P.select(["gsis_id","display_name","draft_year","draft_round","draft_pick","position"]).write_parquet("players_draft.parquet")
nfl.load_player_stats(list(range(2021,2027))).write_parquet("pstats.parquet"); print("datos ok")
