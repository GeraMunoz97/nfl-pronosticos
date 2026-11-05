import pandas as pd
_S=pd.read_parquet("sched.parquet")
def started(gid):
    r=_S[_S.game_id==gid]
    if r.empty: return False
    r=r.iloc[0]; k=pd.Timestamp(f"{r.gameday} {r.gametime}").tz_localize("America/New_York"); return pd.Timestamp.now(tz="UTC")>=k.tz_convert("UTC")
