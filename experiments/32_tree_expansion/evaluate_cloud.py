"""One-case-at-a-time evaluation of frozen forecasts; never fits or changes models."""
from pathlib import Path
from datetime import datetime
import json,hashlib,tarfile,shutil,traceback
import numpy as np
from preprocess_cloud import download
from fields import extract
from alignment import align_reference
from snapshot_evaluation import metrics
import learning_worker
learning_worker.PREFIX='expansion32/evaluation01/'
upload=learning_worker.upload
R=Path(__file__).parent

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 freeze=json.loads((R/'results/prediction-freeze.json').read_text());cases=json.loads((R/'fresh-tests.json').read_text());groups=json.loads((R/'groups.json').read_text());execution=json.loads((R/'test-executions.json').read_text())
 assert len(cases)==48 and len({c['configuration'] for c in cases})==40
 for g in groups:
  if g['phase']=='test':assert datetime.fromisoformat(execution[g['id']]['startTime'].replace('Z','+00:00')).timestamp()>freeze['created_unix']
 for n,h in freeze['files'].items():
  if not n.endswith('.npz'):assert digest(R/n)==h,n
 selected={next(c['case'] for c in cases if c['crown_height_m']==height) for height in [4,6,8,10]};rows=[];histories=[];alignments=[];seed_results=[];models=['snapshot','hybrid','state_reset_ablation'];checks=[]
 for config in sorted({c['configuration'] for c in cases}):
  replicas=[c for c in cases if c['configuration']==config];ensemble=None;expected_forecasts={};seed_h=[]
  for c in replicas:
   n=c['case'];assert c['deck_sha256']==freeze['test_deck_hashes'][n];group=next(g['id'] for g in groups if n in g['cases']);prefix='expansion32/'+group+'/'+n
   archive=R/'data/current.tar.gz';summary=R/'data/current.json';download(prefix+'.summary.json',summary);meta=json.loads(summary.read_text());assert meta['result']['full_horizon'] and meta['resume']['passed'];download(prefix+'.tar.gz',archive);assert digest(archive)==meta['raw_sha256'];dest=R/'data/cloud';dest.mkdir(exist_ok=True)
   with tarfile.open(archive) as tar:
    for member in tar.getmembers():assert not member.name.startswith('/') and '..' not in Path(member.name).parts and not member.issym() and not member.islnk()
    tar.extractall(dest)
   folder=dest/n;assert digest(folder/(n+'.fds'))==c['deck_sha256']
   for rr in meta['checkpoint_manifest']['files']:assert digest(folder/rr['name'])==rr['sha256']
   extract(c);raw=np.load(R/'data/fields'/(n+'.npy'),mmap_mode='r');rawtime=np.load(R/'data/fields'/(n+'-time.npy'));forecasts={};projection={}
   for model in models:
    name=model+'_'+n+'.npz';path=R/'data/predictions'/name;path.parent.mkdir(exist_ok=True);download('expansion32/gpu01/predictions/'+name,path);assert digest(path)==freeze['files']['data/predictions/'+name]
    with np.load(path) as z:pred=z['fields'];tt=z['time']
    if model=='snapshot':
     truth,info=align_reference(raw,rawtime,tt);times=tt;alignments.append(dict(case=n,**info));ensemble=truth.copy()/len(replicas) if ensemble is None else ensemble+truth/len(replicas)
     seed_h.append(dict(seed=c['seed'],HRR_kW=(truth[:,1].sum((1,2,3))*.125).tolist(),peak_C=truth[:,0].max((1,2,3)).tolist()))
     if n in selected:projection['fds']=truth[:,[0,1]].max(axis=3)
    assert np.array_equal(tt,times);rows.append(dict(case=n,configuration=config,seed=c['seed'],model=model,**metrics(truth,pred,times)))
    histories.append(dict(case=n,configuration=config,seed=c['seed'],model=model,time_s=times.tolist(),truth_heat_kW=seed_h[-1]['HRR_kW'],predicted_heat_kW=(pred[:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=seed_h[-1]['peak_C'],predicted_peak_C=pred[:,0].max((1,2,3)).tolist()))
    if len(replicas)>1:
     if model in expected_forecasts:assert np.array_equal(pred,expected_forecasts[model]),'Seed must not change deterministic prediction'
     else:expected_forecasts[model]=pred.copy()
    if n in selected and model!='state_reset_ablation':projection[model]=pred[:,[0,1]].max(axis=3)
    path.unlink()
   if projection:
    p=R/'data'/('projection-'+n+'.npz');np.savez_compressed(p,**projection,time=times);upload(p.name,p.read_bytes());p.unlink()
   checks.append(dict(case=n,raw_sha256=meta['raw_sha256'],solver_wall_seconds=meta['result']['wall_seconds'],deck_sha256=c['deck_sha256']));del raw;shutil.rmtree(folder);archive.unlink()
   for suffix in ['.npy','-time.npy','.json']:(R/'data/fields'/(n+suffix)).unlink()
   print('EVALUATED',n,flush=True)
  if len(replicas)>1:
   h=np.array([s['HRR_kW'] for s in seed_h]);peaks=np.array([s['peak_C'] for s in seed_h]);seed_results.append(dict(configuration=config,seeds=[s['seed'] for s in seed_h],time_s=times.tolist(),FDS_HRR_mean_kW=h.mean(0).tolist(),FDS_HRR_min_kW=h.min(0).tolist(),FDS_HRR_max_kW=h.max(0).tolist(),FDS_peak_min_C=peaks.min(0).tolist(),FDS_peak_max_C=peaks.max(0).tolist(),ensemble_metrics={model:metrics(ensemble,pred,times) for model,pred in expected_forecasts.items()}))
 summary={}
 for model in models:
  summary[model]={}
  for window in ['all','post_source','late']:
   summary[model][window]={}
   for key in rows[0][window]:
    averages=[]
    for config in {c['configuration'] for c in cases}:
     vals=[r[window][key] for r in rows if r['model']==model and r['configuration']==config and r[window][key] is not None]
     if vals:averages.append(float(np.mean(vals)))
    summary[model][window][key]=dict(mean=float(np.mean(averages)),median=float(np.median(averages)),configurations=len(averages)) if averages else None
 result=dict(rows=rows,histories=histories,summary=summary,seed_ensembles=seed_results,reference_alignment=alignments,evidence=checks,fresh_configurations=40,fresh_trajectories=48,prediction_freeze_unix=freeze['created_unix'],projections=sorted(selected),scope='Fixed-grid single generic cone family; not physical validation or multi-tree composition')
 raw=json.dumps(result,indent=2).encode();upload('fresh-test-evaluation.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
