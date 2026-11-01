"""Trace existing gallery points to saved forecast origins; no model fitting or new forecasts."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(folder):
 result=[]
 for p in sorted(folder.glob('page-*.js')):
  s=p.read_text();assert s.startswith('window.receivePage(') and s.endswith(');');result.extend((d,p) for d in json.loads(s[s.index(',')+1:-2]))
 return sorted(result,key=lambda x:x[0]['index'])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--verify-published',action='store_true');args=ap.parse_args();reports={};source={}
 specs=[('denser',R/'data/denser/gallery',R/'data/model-training-results',[(3,None)],'wdavies/fire-reports','denser/gallery/'),('stride_pair',R/'data/pair-gallery',R/'data/pair-sequence-r0-results',[(2,0),(3,1)],'wdavies/fire-reports','stride-one-pair/gallery/'),('old_gated',R.parent/'35_surrogate_diagnostics/attempt24/data/scenario_gallery',R.parent/'35_surrogate_diagnostics/attempt24/data/collected',[(3,None)],'wdavies/fire-prediction-gallery','')]
 for name,folder,saved,arms,repo,prefix in specs:
  rows=records(folder);cache={};examples={};points=0
  for record,page in rows:
   v=np.array(record['values']);truth=v[0];assert v.shape==(4,90,4)
   for series,arm in arms:
    fold=arm if arm is not None else int(record['fold'])*(2 if name=='old_gated' else 1)+(1 if name=='old_gated' else 0)
    if fold not in cache:
     p=saved/f'fold{fold:02}-horizon16-predictions.npz';a=np.load(p);source[str(p.relative_to(R.parents[1]))]=sha(p);cache[fold]=(a,{int(i):j for j,i in enumerate(a['case_indices'])})
    a,index=cache[fold];j=index[int(record['index'])];rolling=a['predicted_physical'][j]
    assert rolling.shape==(75,4) and np.array_equal(v[series,15:],rolling.astype(np.float64)),(name,record['index'],series)
    points+=rolling.size
    # Representative sharp local valley after the initial ramp; no claim it is the user's exact case.
    for f in range(4):
     p=v[series,:,f];normal=max(float(abs(truth[:,f]).max()),[.001,.01,.00001,.1][f]);score=np.minimum(p[:-2]-p[1:-1],p[2:]-p[1:-1])/normal;score[:15]=-np.inf;k=int(np.argmax(score))+1
     key=f'{series}:{f}'
     if key not in examples or score[k-1]>examples[key]['dip_rebound_fraction_of_truth_peak']:
      indices=[k-1,k,k+1];targets=np.array(indices)+1;origins=targets-16
      assert (origins>=0).all()
      trace=[dict(target_step=int(t),target_time_s=float(record['time'][t-1]),origin_step=int(o),origin_time_s=0. if o==0 else float(record['time'][o-1]),lead_steps=16,lead_time_s=float(record['time'][t-1])-(0. if o==0 else float(record['time'][o-1])),plotted_value=float(v[series,t-1,f]),saved_endpoint_value=float(rolling[o,f]),simulation_value=float(truth[t-1,f])) for t,o in zip(targets,origins)]
      examples[key]=dict(case=record['case'],source_id=record['index'],series=series,state=f,local_page=page.name,fold=fold,dip_rebound_fraction_of_truth_peak=float(score[k-1]),trace=trace)
  for p in [folder/'index.html',folder/'report.html']:
   if p.exists():source[str(p.relative_to(R.parents[1]))]=sha(p)
  publication=None
  if args.verify_published:
   from huggingface_hub import HfApi,hf_hub_download
   revision=HfApi().repo_info(repo,repo_type='space').sha;chosen=sorted(set(e['local_page'] for e in examples.values()));checked=[]
   for n in ['index.html']+chosen:
    remote=Path(hf_hub_download(repo,filename=prefix+n,repo_type='space',revision=revision));local=folder/n if n!='index.html' or (folder/n).exists() else folder/'report.html'
    assert remote.read_bytes()==local.read_bytes(),(name,n,'published asset differs; investigate before claiming equivalence');checked.append(dict(path=prefix+n,sha256=sha(remote)))
   import urllib.request
   static_base='https://wdavies-fire-prediction-gallery.static.hf.space/' if repo=='wdavies/fire-prediction-gallery' else 'https://wdavies-fire-reports.static.hf.space/'
   for entry in checked:
    url=static_base+entry['path']
    with urllib.request.urlopen(url,timeout=45) as response:body=response.read()
    assert hashlib.sha256(body).hexdigest()==entry['sha256'],('live static asset differs',url)
    entry['live_static_url']=url;entry['live_static_sha256']=hashlib.sha256(body).hexdigest()
   publication=dict(repo=repo,revision=revision,checked_assets=checked,selected_published_pages_exact=True,live_static_assets_exact=True)
  reports[name]=dict(histories=len(rows),model_curves=len(rows)*len(arms),rolling_values_exact=points,representative_examples=examples,publication=publication)
 for p in [R/'model_evaluation/build_pair_gallery.py',R/'model_evaluation/build_denser.py',R/'data/pair-sequence/rotation0/worker.py',R/'data/model-training/worker.py',R.parent/'35_surrogate_diagnostics/attempt24/build_gallery.py']:
  source[str(p.relative_to(R.parents[1]))]=sha(p)
 out=dict(passed=True,optimizer_updates=0,new_forecasts=0,existing_published_model_outputs_only=True,galleries=reports,source_sha256=source,interpretation='Every checked model value from plotted target16onward is exactly one saved16step forecast endpoint, not an average across forecasts. Origins advance one saved frame. Initial targets1..15 are a single origin0rollout. Each rolling forecast starts from observed simulated history; its subsequent16steps are autonomous. Adjacent plotted endpoints are different forecasts, so a rebound can be a forecast revision. This does not prove every individual dip is caused by refreshing, or establish any model improvement. Representative extrema are selected for explaining construction, not performance or checkpoint selection.')
 (R/'results/gallery-forecast-provenance.json').write_text(json.dumps(out,indent=2)+'\n')
 for name,r in reports.items():
  print(name,'histories',r['histories'],'rolling values exact',r['rolling_values_exact'],'published',r['publication'] is not None)
  e=r['representative_examples']['3:2'];print('gas example',e['case'],e['local_page'],json.dumps(e['trace']))
if __name__=='__main__':main()
