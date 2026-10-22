"""Compare conditional component predictions with FDS; all input heat is from FDS."""
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build import ROOT
D=ROOT/'data/heat-response';O=ROOT/'results/visuals';O.mkdir(exist_ok=True)
cs=json.loads((ROOT/'cases.json').read_text())
for kind in ['single-validation','familiar-pairs']:
 selected=[c for c in cs if (c['family']=='single' and c['split']=='validation') or False] if kind=='single-validation' else [c for c in cs if c['family']=='pair' and c['split'] in ['train','validation']]
 records=[(c,i) for c in selected for i in range(len(c['trees']))]
 fig,axes=plt.subplots(len(records),4,figsize=(15,2.0*len(records)),squeeze=False)
 for row,(c,i) in enumerate(records):
  a=np.load(D/f"{c['case']}__{i}.npz");p=a['state'];q=a['truth'];n=p.shape[1]//2;t=a['time'];pr=a['fuel_rate'].sum(1);qr=a['FDS_fuel_rate'].sum(1)
  pairs=[(q[:,:n].mean(1)*1000+20,p[:,:n].mean(1)*1000+20),(q[:,n:].mean(1),p[:,n:].mean(1)),(qr,pr),(np.r_[0,np.cumsum(qr*2)],np.r_[0,np.cumsum(pr*2)])]
  for col,(truth,pred) in enumerate(pairs):
   ax=axes[row,col];xx=t[:-1] if col==2 else t;ax.plot(xx,truth,color='#222222',label='FDS',lw=1.6);ax.plot(xx,pred,color='#1976ad',label='Conditional recurrent response',lw=1.5);ax.axvspan(0,c['duration'],color='.9',zorder=0);ax.set_xlim(0,180);ax.set_xticks([0,60,120,180]);ax.grid(alpha=.15);ax.tick_params(labelsize=9)
   if row==0:ax.set_title(['Regional mean T (°C)','Mean remaining mass fraction','Fuel vapor (kg/s)','Cumulative fuel vapor (kg)'][col],fontsize=11)
   if col==0:ax.set_ylabel(c['case'].replace('t26_','')+'\n'+c['trees'][i]['type']+(' isolated' if c['family']=='single' else ' source' if i==0 else ' receiver'),fontsize=9)
   if row==len(records)-1:ax.set_xlabel('Time (s)')
 handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.965),ncol=2,frameon=False)
 fig.suptitle('Recorded-heat response: '+kind.replace('-',' '),fontsize=15,y=.99)
 fig.text(.5,.01,'FDS radiation + convection histories supplied as inputs; no FDS state feedback. NOT autonomous composition.\nGeneric fixed canopies; heater-active interval shaded. Fuel-vapor release is not actual gas-phase heat release. Curves show regional means; metrics precede spatial averaging.',ha='center',fontsize=10)
 fig.tight_layout(rect=[0,.05,1,.945]);fig.savefig(O/(kind+'-heat-response.png'),dpi=150);plt.close(fig)
