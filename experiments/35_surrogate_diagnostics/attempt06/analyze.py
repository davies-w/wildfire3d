from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;out=R/'data/visuals';out.mkdir(exist_ok=True);records=[json.loads(p.read_text()) for p in sorted((R/'data/collected').glob('epoch-*.json'))];plan=json.loads((R/'coverage-plan.json').read_text());result={'scope':plan,'epochs':[],'warning':'Temporal interpolation within one realization; historical frozen scales include heldout times. No unseen-case generalization.'}
for r in records:
 assert len(r['rows'])==91 and {x['frame'] for x in r['rows']}==set(range(91))
 summary={}
 for split in ['train','validation_time']:
  for win,pred in [('all',lambda t:True),('ignition',lambda t:t<=20),('post_source',lambda t:t>=22),('late',lambda t:t>=120)]:
   rows=[x for x in r['rows'] if x['split']==split and pred(x['time_s'])];assert rows
   def region(key,count):
    n=sum(x[count] for x in rows);return sum((x[key] or 0)*x[count] for x in rows)/n if n else None
   summary[split+'/'+win]={'objective_MAE':float(np.mean([x['objective_MAE'] for x in rows])),'channel_objective_MAE':np.mean([x['channel_objective_MAE'] for x in rows],axis=0).tolist(),'channel_physical_MAE':np.mean([x['channel_physical_MAE'] for x in rows],axis=0).tolist(),'hot_temperature_MAE_C':region('hot_temperature_MAE_C','hot_cells'),'burning_HRR_MAE_kWm3':region('burning_HRR_MAE_kWm3','burning_cells'),'total_HRR_relative_L1_percent':100*sum(x['HRR_absolute_error_kW'] for x in rows)/max(sum(x['truth_HRR_kW'] for x in rows),1e-8)}
 result['epochs'].append({'epoch':r['epoch'],'mean_training_loss':r['mean_training_loss'],'summary':summary})
fig,axs=plt.subplots(1,3,figsize=(14,4))
for ax,key,title in zip(axs,['objective_MAE','hot_temperature_MAE_C','total_HRR_relative_L1_percent'],['Full-history encoded objective','Post-source hot-region temperature MAE (C)','Post-source total-HRR error (%)']):
 for split in ['train','validation_time']:
  window='all' if key=='objective_MAE' else 'post_source';ax.plot([r['epoch'] for r in result['epochs']],[r['summary'][split+'/'+window][key] for r in result['epochs']],label=split)
 ax.set_title(title);ax.set_xlabel('Complete training epochs');ax.grid(alpha=.25);ax.legend()
fig.suptitle('Coordinate/time fit of one simulated burn; heldout-time interpolation only');fig.tight_layout();fig.savefig(out/'curves.png',dpi=160);plt.close(fig)
if (R/'data/collected/projections.npz').exists():
 z=np.load(R/'data/collected/projections.npz');frames=plan['projection_frames'];fig,axs=plt.subplots(len(frames),4,figsize=(12,12));limits=[max(float(z[k][:,:,ch].max()) for k in z.files) for ch in [0,1]]
 for i,f in enumerate(frames):
  for j,(who,ch) in enumerate([('truth',0),('pred',0),('truth',1),('pred',1)]):
   ax=axs[i,j];im=ax.imshow(z[f'{who}_{f}'][:,:,ch].T,origin='lower',extent=[0,24,0,16],vmin=20 if ch==0 else 0,vmax=limits[ch],cmap='inferno',aspect='equal');ax.set_title(f'{who}: '+('gas T(C)' if ch==0 else 'HRR(kW/m3)')+f' frame{f}');fig.colorbar(im,ax=ax,shrink=.65)
 fig.suptitle('Max-through-y projections, shared scales; not flame geometry');fig.tight_layout();fig.savefig(out/'projections.png',dpi=130);plt.close(fig)
(R/'results/analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['epochs'][-1],indent=2))
