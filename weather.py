# Pronostico automatico de viento por estadio (Open-Meteo: gratuito, sin clave)
import json, urllib.request, pandas as pd
from guard import started
STAD={"ARI":(33.5276,-112.2626,"retr"),"ATL":(33.7554,-84.4008,"retr"),"BAL":(39.2780,-76.6227,"out"),"BUF":(42.7738,-78.7870,"out"),"CAR":(35.2258,-80.8528,"out"),
"CHI":(41.8623,-87.6167,"out"),"CIN":(39.0955,-84.5161,"out"),"CLE":(41.5061,-81.6995,"out"),"DAL":(32.7473,-97.0945,"retr"),"DEN":(39.7439,-105.0201,"out"),
"DET":(42.3400,-83.0456,"dome"),"GB":(44.5013,-88.0622,"out"),"HOU":(29.6847,-95.4107,"retr"),"IND":(39.7601,-86.1639,"retr"),"JAX":(30.3239,-81.6373,"out"),
"KC":(39.0489,-94.4839,"out"),"LV":(36.0909,-115.1833,"dome"),"LAC":(33.9535,-118.3392,"dome"),"LA":(33.9535,-118.3392,"dome"),"MIA":(25.9580,-80.2389,"out"),
"MIN":(44.9737,-93.2577,"dome"),"NE":(42.0909,-71.2643,"out"),"NO":(29.9511,-90.0812,"dome"),"NYG":(40.8135,-74.0745,"out"),"NYJ":(40.8135,-74.0745,"out"),
"PHI":(39.9008,-75.1675,"out"),"PIT":(40.4468,-80.0158,"out"),"SF":(37.4030,-121.9700,"out"),"SEA":(47.5952,-122.3316,"out"),"TB":(27.9759,-82.5033,"out"),
"TEN":(36.1665,-86.7713,"out"),"WAS":(38.9078,-76.8645,"out")}
s=pd.read_parquet("sched.parquet"); c=s[s.result.isna()&s.spread_line.notna()].sort_values("gameday")
if c.empty: raise SystemExit
S,W=c.iloc[0].season,c.iloc[0].week; wk=s[(s.season==S)&(s.week==W)&s.result.isna()]
wind=json.load(open("state/wind.json")); roof=json.load(open("state/roof.json"))
for r in wk.itertuples():
    if started(r.game_id) or r.location!="Home" or r.home_team not in STAD: continue
    lat,lon,kind=STAD[r.home_team]
    if kind=="dome": continue
    if kind=="retr": roof[r.game_id]="closed"; continue        # techo retractil: se asume cerrado
    k=pd.Timestamp(f"{r.gameday} {r.gametime}").tz_localize("America/New_York").tz_convert("UTC")
    if (k-pd.Timestamp.now(tz="UTC")).days>6: continue          # el pronostico solo es util a pocos dias
    url=(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=wind_speed_10m&wind_speed_unit=mph&timezone=UTC"
         f"&start_date={k.strftime('%Y-%m-%d')}&end_date={k.strftime('%Y-%m-%d')}")
    try:
        d=json.load(urllib.request.urlopen(url,timeout=20)); h=d["hourly"]
        i=min(range(len(h["time"])),key=lambda j:abs(pd.Timestamp(h["time"][j]).tz_localize("UTC")-k))
        wind[r.game_id]=round(float(h["wind_speed_10m"][i]),1); print("viento",r.game_id,wind[r.game_id],"mph")
    except Exception as e: print("sin pronostico",r.game_id,e)
json.dump(wind,open("state/wind.json","w")); json.dump(roof,open("state/roof.json","w"))
