"""Five-chart selected-model case plot, only from verified final collection."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--case-index',type=int,required=True);p.add_argument('--output',required=True);args=p.parse_args()
assert json.loads((R/'results03/collected.json').read_text())['passed']
a=np.load(R/'data/training/data/sequences.npz');cones=np.load(R/'data/training/data/cones.npz');pr=np.load(R/'data/pool03-results/fold00-test-predictions.npz');ids=pr['case_indices'];where=np.flatnonzero(ids==args.case_index);assert len(where)==1;i=int(where[0]);n=args.case_index
pred=np.sinh(pr['normalized_rollout'][i]*pr['std']+pr['mean'])*pr['physical_scales'];t=a['time'][n];fig,axes=plt.subplots(1,5,figsize=(24,4.5))
for j,(ax,label) in enumerate(zip(axes[:4],['Water (kg)','Fuel (kg)','Gas (kg/s)','Heating index (K)'])):
 ax.plot(t,a['state'][n,:,j],color='#334155',label='Simulation');ax.plot(t[1:],pred[:,j],color='#2563eb',ls='--',label='Prediction');ax.set(title=label,xlabel='Time (s)');ax.grid(alpha=.2);ax.legend(fontsize=8)
ax=axes[4];other=ax.twinx();truth=cones['parameters'][n,1:];guess=pr['cone_parameters'][i];ta=cones['active'][n,1:];pa=pr['cone_presence_probability'][i]>=.5
for target,mask,style,tag in [(truth,ta,'-','Extracted'),(guess,pa,'--','Predicted')]:
 ax.plot(t[1:],np.where(mask,target[:,2],np.nan),color='#2563eb',ls=style,label=tag+' length')
 other.plot(t[1:],np.where(mask,target[:,4],np.nan),color='#dc2626',ls=style,label=tag+' peak temperature')
ax.set(title='Cone length / peak temperature',xlabel='Time (s)',ylabel='Axial length (m)');other.set_ylabel('Peak inside cone (°C)');ax.grid(alpha=.2);h,l=ax.get_legend_handles_labels();h2,l2=other.get_legend_handles_labels();ax.legend(h+h2,l+l2,fontsize=7)
for axis in axes:axis.set_xlim(float(t[0]),float(t[-1]))
fig.suptitle('Case '+str(n)+' · solid reference, dashed prediction; cone gaps mean absent (prediction threshold 0.5)');fig.tight_layout();fig.savefig(args.output,dpi=130)
