from pathlib import Path
import yaml
repo=Path('/Users/wdavies/pi/wildfire3d');r=repo/'experiments/35_surrogate_diagnostics/attempt16';old=r.parent/'attempt15'
s=(r/'worker.py').read_text().replace('3516+k*10000+epoch',"3516+rotation['rotation']*10000+epoch")
s=s.replace("result[str(h)]=dict(steps=h,nominal_seconds=2*h,model_MAE=aggregate(parts),no_change_MAE=aggregate(hold),mean_absolute_truth=aggregate(truths),scope='All valid forecast origins; observed history through origin, predictions thereafter')",'''errors=torch.cat(parts).reshape(len(ids),91-h,3);hold_errors=torch.cat(hold).reshape(len(ids),91-h,3)
  finite=bool(torch.isfinite(errors).all())
  windows={'ignition':times[ids,h:]<=20,'post_source_to90':(times[ids,h:]>20)&(times[ids,h:]<=90),'after90':times[ids,h:]>90,'active':active[ids,h-1:],'quiet':~active[ids,h-1:]}
  result[str(h)]=dict(steps=h,nominal_seconds=2*h,finite=finite,model_MAE=aggregate(parts) if finite else None,no_change_MAE=aggregate(hold),mean_absolute_truth=aggregate(truths),model_windows={w:phase_mae(errors,m,ids) if finite else None for w,m in windows.items()},no_change_windows={w:phase_mae(hold_errors,m,ids) for w,m in windows.items()},scope='All valid forecast origins; observed history through origin, predictions thereafter; windows by endpoint')''')
(r/'worker.py').write_text(s)
# Proven data and normalization tests plus memory-specific behavioral tests.
s=(old/'validate.py').read_text();start=s.index('m=Transition();');s=s[:start]+'''checks=[]
for kind in ['mlp','gru']:
 m=Transition(kind);x=ns['history_at'](z,ids[:4],torch.zeros(4,dtype=torch.long));u=external[ids[:4],0];y,mem=m.step(x,u);assert torch.equal(y,x[:,-1])
 # Nonzero readout exercises recurrent dependence, without any optimizer.
 with torch.no_grad():
  head=m.head if kind=='gru' else m.net[-1];head.weight.fill_(.001)
 y,mem=m.step(x,u);buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);m2=Transition(kind);m2.load_state_dict(torch.load(buf,weights_only=False));assert torch.equal(m2(x,u),y)
 hist=x;memory=None;loss=0
 for j in range(32):
  pred,memory=m.step(hist,external[ids[:4],j],memory);loss+=ns['objective'](pred,z[ids[:4],j+1]).mean();hist=ns['advance'](hist,pred)
 loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters())
 if kind=='gru':assert m.cell.weight_hh.grad.abs().sum()>0
 original=ns['predictions'](m,z,ids[:3],True);mutated=z.clone();mutated[:,1:]+=100;assert torch.equal(original,ns['predictions'](m,mutated,ids[:3],True))
 # Teacher-forced prefix memory must be independent of states beyond origin.
 js=torch.tensor([4,8,12]);ii=ids[:3];first=ns['prefix_memory'](m,z,ii,js);alt=z.clone()
 for n,j in zip(ii.tolist(),js.tolist()):alt[n,j+1:]+=100
 second=ns['prefix_memory'](m,alt,ii,js)
 if kind=='gru':assert torch.equal(first,second)
 out=ns['evaluate'](m,z,ii,mean,std,True);assert out['rollout']['finite']
 # At horizon one, cached GRU teacher-memory equals direct sequential evaluation.
 one=ns['predictions'](m,z,ii,False)
 for j in [0,4,30,89]:
  jj=torch.full_like(ii,j);h0=ns['history_at'](z,ii,jj);hmem=ns['prefix_memory'](m,z,ii,jj);direct,_=m.step(h0,external[ii,j],hmem);assert torch.allclose(direct,one[:,j],atol=1e-6,rtol=1e-6)
 checks.append(dict(kind=kind,parameters=sum(p.numel() for p in m.parameters()),checks=['initial persistence','32step backward all parameters finite','serialization exact','no future truth in autonomous or prefix','one-step cached memory equivalence']))
for h in [1,8,16,32]:
 count=np.zeros(90,int)
 for j in range(0,90,h):count[j:min(j+h,90)]+=1
 assert (count==1).all()
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,local_training=False,histories=520,configurations=480,checks=checks,matched_shuffle='same rotation/epoch seed for both arms',split_normalization_tests=True),indent=2));print('PREFLIGHT PASSED',checks)
''';s=s.replace("'predictions','evaluate'","'prefix_memory','predictions','evaluate'");(r/'validate.py').write_text(s)
(r/'analyze.py').write_text('''"""Compare two architectures on fixed grouped folds and forecast horizons."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;r=json.loads((R/'data/collected/report.json').read_text());v=R/'data/visuals';v.mkdir(exist_ok=True)
assert len(r['folds'])==len(r['tests'])==20
summary={'scope':r['scope'],'arms':{},'folds':[{k:f[k] for k in ['kind','rotation','epochs','selected_epoch','stop_reason']} for f in r['folds']]}
for kind in ['mlp','gru']:
 folds=[f for f in r['folds'] if f['kind']==kind];tests=[f for f in r['tests'] if f['kind']==kind]
 for feature,label in [(None,'Normalized MSE'),(0,'Water MAE kg'),(1,'Dry-fuel MAE kg'),(2,'Fuel-gas release MAE kg/s')]:
  fig,axes=plt.subplots(2,5,figsize=(20,8))
  for ax,f in zip(axes.flat,folds):
   for split in ['train','validation']:
    h=f['history'];y=[x[split]['rollout'].get('objective',np.nan) if feature is None else (x[split]['rollout'].get('physical_MAE_by_feature') or [np.nan]*3)[feature] for x in h];ax.plot([x['epoch'] for x in h],y,label=split)
   ax.set_yscale('log');ax.axvline(f['selected_epoch'],ls=':',color='black');ax.set_title(f"Fold{f['rotation']} {f['stop_reason']}");ax.set_xlabel('Epoch');ax.set_ylabel(label);ax.legend()
  fig.suptitle(kind+' full autonomous rollouts; log scale; selected epoch dotted');fig.tight_layout();fig.savefig(v/f'{kind}-{feature}.png',dpi=140);plt.close(fig)
 summary['arms'][kind]={'tests':tests,'rollout_MAE_equal_fold_mean':np.mean([x['metrics']['rollout']['physical_MAE_by_feature'] for x in tests],axis=0).tolist(),'one_step_MAE_equal_fold_mean':np.mean([x['metrics']['one_step']['physical_MAE_by_feature'] for x in tests],axis=0).tolist()}
fig,axes=plt.subplots(1,3,figsize=(15,4))
for k,label in enumerate(['Water kg','Dry fuel kg','Release kg/s']):
 for kind in ['mlp','gru']:
  tests=summary['arms'][kind]['tests'];hs=[1,4,8,16,45];ys=[np.mean([t['horizons'][str(h)]['model_MAE'][k] if t['horizons'][str(h)]['finite'] else np.nan for t in tests]) for h in hs];axes[k].plot(np.array(hs)*2,ys,'o-',label=kind)
 hold=[np.mean([t['horizons'][str(h)]['no_change_MAE'][k] for t in tests]) for h in hs];axes[k].plot(np.array(hs)*2,hold,'--',label='No change');axes[k].set_xlabel('Forecast horizon seconds');axes[k].set_ylabel(label);axes[k].legend()
fig.tight_layout();fig.savefig(v/'horizon-errors.png',dpi=150);plt.close(fig)
(R/'results/analysis.json').write_text(json.dumps(summary,indent=2))
''')
d=yaml.safe_load((old/'dvc.yaml').read_text());d['stages']['prepare_data']={'cmd':'../../../.venv/bin/python prepare.py','deps':['prepare.py','../attempt15/data/sequences.npz','../attempt15/schema.json'],'outs':['data/sequences.npz',{'schema.json':{'cache':False}}]};del d['stages']['percentage_errors'];(r/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(r/'README.md').write_text('''# Matched finite-history versus GRU memory — attempt16

User authorized this controlled comparison after the three-state model beat current-state persistence during20–90s but drifted when chained. Same520 histories/480 configurations and grouped ten 8/1/1 splits as15; seed replicas stay together. All20 validation-selected models freeze before tests. Previously examined and reshuffled simulations are not historically pristine tests.

Exactly three measured evolving states: derived remaining water kg, unreacted dry vegetation kg, vegetation fuel-gas release kg/s (not heat). Char treated as inert ash. Same derived labels/yield0.75, including small negative water integration residuals; no new simulations or label changes.

Both arms receive [batch,21]: last four three-state observations/predictions plus nine known external/static values (height, loading, +X wind speed, cos/sin ignition angle, initial water/dryfuel, ignition-on fraction, dt). Output [batch,3]. MLP21→64SiLU→64SiLU→3 (5,763parameters). GRUCell21→32 plus32→3 readout (5,379parameters) also carries [batch,32] internal memory initialized zero. This internal memory is not32 additional measured states or identifiable heat content. No change to the agreed physical outputs. Both fresh, zero readout means identical initial persistence predictions; architectures have different weights. Same rotation/epoch shuffle, normalization, loss, optimizer and sequence curriculum. Within an architecture identical initialweights across folds.

Every epoch covers90 transitions per history once, with shorter final window where needed. Horizon1 for epochs1–20,8 for21–40,16 for41–60,32 thereafter. GRU memory at each training window is recomputed from observed prefix using current weights under no_grad; gradients flow through the predicted window only. This truncated training does not teach long-prefix memory through full-history gradients. Autonomous evaluation initializes from time0 and uses predicted history/memory exclusively. One-step evaluation uses observed history; horizon tests start at every valid measured origin then feed predictions. Evaluate2/8/16/32/90s-ahead with no-change baseline and active/quiet/time windows by endpoint. This separates next-step accuracy from accumulation of error.

Same train-only asinh normalization and equal active/quiet training weighting as15. AdamW3e-4, min100 max400epochs; validation patience30, reset at21/41/61, minvalidation full-rollout objective checkpoint. Every epoch fulltrain/fullvalidation one-step and180s rollout. Selected checkpoint may precede final curriculum phase; report its horizon explicitly. No positivity/monotonicity/conservation clipping; report invalid states. No automatic architecture choice from aggregate loss alone.

Completed-epoch checkpoints include optimizer/RNG/history/selection; resumable separate reservation/new prefix only after diagnosis. All completedfold reports/selectedweights preserved. CUDA serialization/gradient checks mandatory; CPU tests never optimize. Expected$2–4.50,maximum$6allowance; six-hour task,6h05VM,6h30absolute,5h40softstop,20minqueue. Runtime cost replaces allowance, later matching billed rows replace estimates. No blind retries. Temporary exact-object24h input access removed by collector; verify VM/job/disks empty. DVC stages submit/collect/analyze; all code/workflowgenerators/checkpoints archived to approved public HF and GitHub.

Generic3mwide cones4/6/8/10m above2m,1600weightedparticles,.5m24x16x16m domain180s,1500C20s source,no trunks/buildings/embers;48legacy geometries retain documentation. Not heat release/plume/real-world validation. Source data remain unchanged.
''')
