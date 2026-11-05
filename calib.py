import json, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from scipy.stats import norm
H=pd.DataFrame(json.load(open("history.json"))); S=pd.read_parquet("sched.parquet")[["game_id","home_moneyline","away_moneyline"]].rename(columns={"game_id":"id"}); H=H.merge(S,on="id",how="left")
MT=json.load(open("state/margin_table.json")); grid=np.array(MT["grid"]); T=np.array(MT["t"]); vals=np.arange(MT["lo"],MT["lo"]+T.shape[1])
row=lambda m: T[int(np.clip(round((m-grid[0])*2),0,len(grid)-1))]; pgt=lambda m,L: row(m)[vals>L].sum(); peq=lambda m,L: row(m)[vals==L].sum() if float(L).is_integer() else 0.0
def imp(a): a=np.asarray(a,float); return np.where(a>0,100/(a+100),np.where(a<0,-a/(-a+100),np.nan))
res=H.hs-H["as"]; tot=H.hs+H["as"]; out={}
def summ(name,p,pm,y,bins):
    k=~np.isnan(y)&~np.isnan(pm); p,pm,y=p[k],pm[k],y[k]; bm=float(np.mean((p-y)**2)); bk=float(np.mean((pm-y)**2)); cal=[]
    for lo,hi in zip(bins[:-1],bins[1:]):
        s=(p>=lo)&(p<hi)
        if s.sum()>=25: cal.append([round(float(p[s].mean()),3),round(float(y[s].mean()),3),int(s.sum())])
    out[name]={"n":int(k.sum()),"brier":round(bm,5),"brier_mkt":round(bk,5),"skill":round((1-bm/bk)*100,2),"cal":cal}
pw=np.array([pgt(m,0)+0.5*peq(m,0) for m in H.m]); ih,ia=imp(H.home_moneyline),imp(H.away_moneyline); pmk=ih/(ih+ia); pmk=np.where(np.isnan(pmk),norm.cdf(H.sl/13),pmk)
y=np.where(res>0,1.0,np.where(res<0,0.0,np.nan)); fav=pw>=0.5; summ("ganador",np.where(fav,pw,1-pw),np.where(fav,pmk,1-pmk),np.where(fav,y,1-y),[.5,.55,.6,.65,.7,.75,.8,.85,.9,1.01])
pc=np.array([pgt(m,sl)/max(1e-9,1-peq(m,sl)) for m,sl in zip(H.m,H.sl)]); yc=np.where(res>H.sl,1.0,np.where(res<H.sl,0.0,np.nan)); sd=pc>=0.5
summ("spread",np.where(sd,pc,1-pc),np.full(len(pc),.5),np.where(sd,yc,1-yc),[.5,.52,.54,.56,.58,.6,.65,1.01])
po=1-norm.cdf((H.tl-H.t)/13.3); yo=np.where(tot>H.tl,1.0,np.where(tot<H.tl,0.0,np.nan)); so=po>=0.5; summ("total",np.where(so,po,1-po),np.full(len(po),.5),np.where(so,yo,1-yo),[.5,.52,.54,.56,.58,.6,1.01])
tp=[];ty=[]
for tdl in H.td:
    for z in (tdl or []): tp.append(z[2]); ty.append(z[3])
tp=np.array(tp); ty=np.array(ty,float); summ("td",tp,np.full(len(tp),ty.mean()),ty,[0,.25,.3,.35,.4,.45,.5,.55,.6,.7,1.01])
json.dump(out,open("state/calib.json","w"),ensure_ascii=False); print("calib ok",{k:v["skill"] for k,v in out.items()})
