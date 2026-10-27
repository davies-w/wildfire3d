"""Descriptive condition associations in saved forecasts; no fitting or selection."""
from pathlib import Path
import json,csv
import numpy as np
R=Path(__file__).resolve().parents[1]
FIELDS=['water','dry_fuel','gas_release','heating_index'];CONDITIONS=['height','moisture','loading','wind','angle']
def analyze(root,meta_path,data_path,folds):
 meta=json.loads(meta_path.read_text());a=np.load(data_path);state=a['state'];configs=a['configuration'];rows=[]
 for fold in folds:
  for h in [8,16]:
   p=root/f'fold{fold:02}-horizon{h:02}-predictions.npz'
   if not p.exists():continue
   z=np.load(p);ids=z['case_indices'];pred=z['predicted_physical'];truth=state[ids,h:];assert pred.shape==truth.shape
   for j,i in enumerate(ids):
    # Differences relative to each trajectory's own truth peak, not tiny instantaneous denominators.
    err=pred[j]-truth[j];peak=np.max(np.abs(state[i]),axis=0);safe=np.maximum(peak,1e-12)
    # Compare prediction AT the true gas/heating peak, rather than unaligned maxima.
    peak_ids=np.argmax(truth[j],axis=0);at_peak=err[peak_ids,np.arange(4)]/safe
    row=dict(case=meta['cases'][i]['case'],configuration=int(configs[i]),fold=fold,horizon_steps=h,conditions=meta['cases'][i]['physical_key'],mean_signed_fraction=(err.mean(0)/safe).tolist(),peak_time_signed_fraction=at_peak.tolist(),worst_under_fraction=(np.maximum(-err,0).max(0)/safe).tolist(),truth_peak=peak.tolist())
    rows.append(row)
 report={}
 for h in [8,16]:
  rr=[r for r in rows if r['horizon_steps']==h];groups={}
  for r in rr:groups.setdefault(r['configuration'],[]).append(r)
  pooled=[]
  for cc,rs in groups.items():
   pooled.append(dict(case=rs[0]['case'],conditions=rs[0]['conditions'],worst=np.mean([r['worst_under_fraction'] for r in rs],axis=0),peak=np.mean([r['peak_time_signed_fraction'] for r in rs],axis=0),signed=np.mean([r['mean_signed_fraction'] for r in rs],axis=0)))
  if not pooled:continue
  worst=np.array([r['worst'] for r in pooled]);threshold=np.quantile(worst,.9,axis=0);conditions={}
  for k,name in enumerate(CONDITIONS):
   conditions[name]={}
   for val in sorted(set(r['conditions'][k] for r in pooled)):
    ix=[j for j,r in enumerate(pooled) if r['conditions'][k]==val];w=worst[ix]
    conditions[name][str(val)]={'n_configurations':len(ix),'median_worst_under_fraction':np.median(w,axis=0).tolist(),'top_decile_rate':np.mean(w>=threshold,axis=0).tolist(),'median_peak_time_signed_fraction':np.median([pooled[j]['peak'] for j in ix],axis=0).tolist()}
  report[str(h*2)]={'histories':len(rr),'configurations':len(pooled),'top_decile_threshold':threshold.tolist(),'condition_groups':conditions,'worst_gas_examples':[dict(case=pooled[j]['case'],conditions=pooled[j]['conditions'],worst_under_fraction=pooled[j]['worst'].tolist(),peak_time_signed_fraction=pooled[j]['peak'].tolist()) for j in np.argsort(worst[:,2])[-12:][::-1]]}
 return report

def smoothness():
 a=np.load(R/'data/learning/sequences.npz');meta=json.loads((R/'learning-schema.json').read_text());lookup={c['case']:i for i,c in enumerate(meta['cases'])};rows=[]
 for folder in sorted((R/'data/verified-material').iterdir()):
  files=list(folder.glob('*_devc.csv'))
  if not files or folder.name not in lookup:continue
  with files[0].open() as f:r=list(csv.reader(f))
  names=r[1];v=np.array(r[2:],float);gas=v[:,[j for j,n in enumerate(names) if n.startswith('v0 fuel')]].sum(1);i=lookup[folder.name];t=a['time'][i];sample=a['state'][i,:,2];expected=np.interp(t,v[:,0],gas)
  tv=float(np.abs(np.diff(gas)).sum());stv=float(np.abs(np.diff(sample)).sum());peak=float(gas.max());rows.append(dict(case=folder.name,n_device_samples=len(gas),n_gallery_samples=len(sample),median_device_interval_s=float(np.median(np.diff(v[:,0]))),max_extraction_gas_difference=float(abs(expected-sample).max()),raw_peak=peak,sampled_peak=float(sample.max()),sampled_to_raw_peak=float(sample.max()/peak) if peak>0 else None,total_variation_retained=stv/tv if tv>0 else None))
 return {'n':len(rows),'rows':rows}
def main():
 old=R.parent/'35_surrogate_diagnostics/attempt24'
 sets={'old_gated_tenfold':(old/'data/collected',old/'schema.json',old/'data/sequences.npz',range(1,20,2)), 'dense_plain_tenfold':(R/'data/model-training-results',R/'learning-schema.json',R/'data/learning/sequences.npz',range(10))}
 for rot in [0]:
  for arm,fold in [('plain',0),('gated',1)]:sets[f'stride_one_r{rot}_{arm}']=(R/f'data/pair-sequence-r{rot}-results',R/f'data/pair-sequence/rotation{rot}/schema.json',R/'data/learning/sequences.npz',[fold])
 out={'scope':'Descriptive post-hoc associations, not causal or pristine confirmation. No training, no new simulations. Equal configuration means across replicas. Worst negative error across forecast origins normalized by full-history absolute truth peak per state. 16/32s horizons are nominal; initial gallery ramp is not included in these rolling-origin metrics. Marginal conditions may be confounded; variable counts explicit.','states':FIELDS,'datasets':{k:analyze(*v) for k,v in sets.items()},'smoothness':smoothness()}
 (R/'results/undershoot-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')
 for label,res in out['datasets'].items():
  if '32' not in res:continue
  d=res['32'];print(label,d['configurations'],'configs')
  for condition,groups in d['condition_groups'].items():print(condition,[(k,round(v['median_worst_under_fraction'][2],3),round(v['top_decile_rate'][2],3),v['n_configurations']) for k,v in groups.items()])
 s=out['smoothness'];print('raw cases',s['n']);print('gas extraction max',max(r['max_extraction_gas_difference'] for r in s['rows']));print('median TV retained',np.median([r['total_variation_retained'] for r in s['rows'] if r['total_variation_retained'] is not None]))
if __name__=='__main__':main()
