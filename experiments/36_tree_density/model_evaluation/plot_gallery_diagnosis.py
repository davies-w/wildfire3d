"""Plot exact gallery curves and marginal condition summaries from the audit."""
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from diagnose_undershoots import R

def main():
 d=json.loads((R/'results/gallery-undershoot-diagnosis.json').read_text());D=R/'data/undershoot-diagnosis';D.mkdir(exist_ok=True)
 fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
 for label in ['dense_plain','stride_plain','stride_gated']:
  for ax,key in zip(axs,['moisture','loading']):
   groups=d[label]['conditions'][key];xx=[float(k) for k in groups];yy=[100*g['median_worst_under'][2] for g in groups.values()];ax.plot(xx,yy,'o-',label=label)
 axs[0].set_xlabel('Initial water / dry fuel');axs[1].set_xlabel('Fuel loading multiplier')
 for ax in axs:ax.set_ylabel('Median worst gas undershoot / truth peak (%)');ax.legend(fontsize=8);ax.grid(alpha=.2)
 fig.suptitle('Exact displayed curves: early autonomous rollout + later refreshed forecasts');fig.savefig(D/'gallery-conditions.png',dpi=160);plt.close(fig)
 # Same representative case as raw audit, plotted with every displayed prediction including startup.
 case='x36_1522_s0';record=None
 for p in (R/'data/pair-gallery').glob('page-*.js'):
  s=p.read_text();rr=json.loads(s[s.index(',')+1:s.rindex(')')]);record=next((r for r in rr if r['case']==case),record)
 assert record is not None
 folder=R/'data/verified-material'/case
 with (folder/(case+'_devc.csv')).open() as f:rr=list(csv.reader(f))
 names=rr[1];v=np.array(rr[2:],float);cols=[j for j,k in enumerate(names) if k.startswith('v0 fuel')];fig,axs=plt.subplots(2,1,figsize=(11,7),layout='constrained');axs[0].plot(v[:,0],v[:,cols].sum(1),label='Retained device sum (~1 s)',color='#555',lw=1)
 for k,label,color in [(0,'Gallery simulation (~2 s)','#159447'),(2,'Plain GRU','#e67e13'),(3,'Gated GRU','#1878c8')]:axs[0].plot(record['time'],np.array(record['values'][k])[:,2],label=label,color=color,lw=1.3)
 axs[0].axvspan(0,32,color='black',alpha=.06,label='Initial autonomous ramp (~32 s)');axs[0].set_title(case+' · 10 m crown above 2 m base; 30% water/dry fuel; wind 3 m/s; ignition 315°')
 for j in cols:axs[1].plot(v[:,0],v[:,j],label=names[j])
 axs[1].set_title('Retained fuel-class device signals before summation')
 for ax in axs:ax.set_xlim(0,80);ax.set_ylabel('Fuel-gas release (kg/s)');ax.set_xlabel('Simulation time (s)');ax.legend(fontsize=8);ax.grid(alpha=.2)
 fig.savefig(D/'gallery-raw-comparison.png',dpi=160);plt.close(fig)
 print(D)
if __name__=='__main__':main()
