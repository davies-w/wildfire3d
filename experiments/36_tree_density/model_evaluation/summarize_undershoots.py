"""Matched descriptive checks and figures for saved-test undershoot diagnosis."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from diagnose_undershoots import R,FIELDS

def paired_condition(d,k,low,high):
 groups={}
 for r in d:
  c=r['conditions'];key=tuple(c[:k]+c[k+1:]);groups.setdefault(key,{})[c[k]]=r
 pairs=[(v[low],v[high]) for v in groups.values() if low in v and high in v]
 if not pairs:return {'matched_pairs':0}
 x=np.array([a['worst'] for a,b in pairs]);y=np.array([b['worst'] for a,b in pairs])
 return {'matched_pairs':len(pairs),'median_low':np.median(x,axis=0).tolist(),'median_high':np.median(y,axis=0).tolist(),'median_paired_high_minus_low':np.median(y-x,axis=0).tolist(),'fraction_high_worse':np.mean(y>x,axis=0).tolist()}
def main():
 old=R.parent/'35_surrogate_diagnostics/attempt24';data=np.load(R/'data/learning/sequences.npz');meta=json.loads((R/'learning-schema.json').read_text());configs=data['configuration'];out={};all_rows={}
 specs=[('old_gated',old/'data/collected',old/'data/sequences.npz',old/'schema.json',list(range(1,20,2))),('dense_plain',R/'data/model-training-results',R/'data/learning/sequences.npz',R/'learning-schema.json',list(range(10))),('stride_plain',R/'data/pair-sequence-r0-results',R/'data/learning/sequences.npz',R/'data/pair-sequence/rotation0/schema.json',[0]),('stride_gated',R/'data/pair-sequence-r0-results',R/'data/learning/sequences.npz',R/'data/pair-sequence/rotation0/schema.json',[1])]
 for label,root,ap,mp,folds in specs:
  a=np.load(ap);m=json.loads(mp.read_text());rows=[]
  for fold in folds:
   h=np.load(root/f'fold{fold:02}-horizon16-predictions.npz');full=np.load(root/f'fold{fold:02}-test-predictions.npz');ids=h['case_indices'];assert np.array_equal(ids,full['case_indices']);truth=a['state'][ids];roll=np.sinh(full['normalized_rollout']*full['std']+full['mean'])*full['physical_scales'];pred=h['predicted_physical'];tt=truth[:,16:];peaks=np.maximum(np.abs(truth).max(1),1e-12)
   for j,i in enumerate(ids):
    peakidx=int(np.argmax(tt[j,:,2]));predpeakidx=int(np.argmax(pred[j,:,2]));row=dict(case=m['cases'][i]['case'],conditions=m['cases'][i]['physical_key'],config=int(a['configuration'][i]),worst=(np.maximum(tt[j]-pred[j],0).max(0)/peaks[j]).tolist(),full_worst=(np.maximum(truth[j,1:]-roll[j],0).max(0)/peaks[j]).tolist(),gas_peak_bias=float((pred[j,:,2].max()-tt[j,:,2].max())/peaks[j,2]),gas_peak_time_offset_s=float(a['time'][i,16+predpeakidx]-a['time'][i,16+peakidx]))
    rows.append(row)
  groups={}
  for r in rows:groups.setdefault(r['config'],[]).append(r)
  pooled=[]
  for rs in groups.values():
   p={k:rs[0][k] for k in ['case','conditions']}
   for k in ['worst','full_worst','gas_peak_bias','gas_peak_time_offset_s']:p[k]=np.mean([r[k] for r in rs],axis=0).tolist()
   pooled.append(p)
  all_rows[label]=pooled;w=np.array([r['worst'] for r in pooled]);cut=np.quantile(w[:,2],.9);bad=[r for r in pooled if r['worst'][2]>=cut]
  out[label]={'configurations':len(pooled),'matched_moisture_6_vs_30':paired_condition(pooled,1,.06,.3),'matched_loading_07_vs_13':paired_condition(pooled,2,.7,1.3),'top_gas_decile':{'n':len(bad),'median_peak_amplitude_bias':float(np.median([r['gas_peak_bias'] for r in bad])),'median_absolute_peak_time_offset_s':float(np.median([abs(r['gas_peak_time_offset_s']) for r in bad]))},'full_rollout_median_worst_under_fraction':np.median([r['full_worst'] for r in pooled],axis=0).tolist()}
 # Compare same test configurations to avoid claiming more data / gating cause improvement across unmatched tests.
 x={r['case']:r for r in all_rows['stride_plain']};y={r['case']:r for r in all_rows['stride_gated']};assert x.keys()==y.keys()
 delta=np.array([np.array(y[k]['worst'])-np.array(x[k]['worst']) for k in x]);out['paired_gated_minus_plain']={'configurations':len(x),'median_change':np.median(delta,axis=0).tolist(),'fraction_gated_lower_under':np.mean(delta<0,axis=0).tolist()}
 D=R/'data/undershoot-diagnosis';D.mkdir(exist_ok=True)
 fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
 for label in ['dense_plain','stride_plain','stride_gated']:
  rr=all_rows[label]
  for ax,k,vs in [(axs[0],1,[.06,.12,.18,.24,.3]),(axs[1],2,[.7,1.,1.3])]:
   vals=[np.median([r['worst'][2] for r in rr if r['conditions'][k]==v])*100 for v in vs];ax.plot(vs,vals,'o-',label=label)
 axs[0].set_xlabel('Initial water / dry fuel');axs[1].set_xlabel('Fuel loading multiplier')
 for ax in axs:ax.set_ylabel('Median worst gas undershoot / truth peak (%)');ax.legend(fontsize=8);ax.grid(alpha=.2)
 fig.suptitle('32-second rolling forecasts; marginal, post-hoc associations');fig.savefig(D/'conditions.png',dpi=160);plt.close(fig)
 # Worst gated case: retained one-second device sum vs two-second gallery truth and rolling forecast.
 case=max(all_rows['stride_gated'],key=lambda r:r['worst'][2])['case'];folder=R/'data/verified-material'/case
 import csv
 with (folder/(case+'_devc.csv')).open() as f:csvrows=list(csv.reader(f))
 names=csvrows[1];v=np.array(csvrows[2:],float);cols=[j for j,n in enumerate(names) if n.startswith('v0 fuel')];gas=v[:,cols].sum(1);idx=next(i for i,c in enumerate(meta['cases']) if c['case']==case);fig,axs=plt.subplots(2,1,figsize=(11,7),layout='constrained');axs[0].plot(v[:,0],gas,label='Retained device sum (~1 s)',lw=1);axs[0].plot(data['time'][idx],data['state'][idx,:,2],'o-',ms=2,label='Extracted gallery truth (~2 s)',lw=1)
 for arm,label in [(0,'Plain GRU'),(1,'Gated GRU')]:
  z=np.load(R/f'data/pair-sequence-r0-results/fold{arm:02}-horizon16-predictions.npz');j=int(np.flatnonzero(z['case_indices']==idx)[0]);axs[0].plot(data['time'][idx,16:],z['predicted_physical'][j,:,2],label=label+' rolling 32 s')
 for j in cols:axs[1].plot(v[:,0],v[:,j],label=names[j])
 axs[0].set_title(case+' · 10 m crown, 30% dry-basis moisture, loading 1.0, wind 3 m/s, ignition 315°');axs[1].set_title('Fuel-class contributions before summation (already device outputs)')
 for ax in axs:ax.set_xlabel('Simulation time (s)');ax.set_ylabel('Fuel-gas release (kg/s)');ax.legend(fontsize=8);ax.grid(alpha=.2)
 fig.savefig(D/'raw-and-predictions.png',dpi=160);plt.close(fig)
 out['scope']='Post-hoc saved tests, not causal evidence. Matched pairs hold other four recorded conditions equal; different seeds/fold models can still differ. Worst undershoot divided by full-history truth peak. Full autonomous rollouts are separate from gallery rolling forecasts. No new solver, fitting, or held-out model selection.'
 (R/'results/undershoot-matched-checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
