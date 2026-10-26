"""Audit all three newly identified preemptions and preserve completed case evidence."""
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from cloud import R,G,BUCKET,gc,read,download_summary
for k in (88,93,115):
 name=f'x36-density-{k:03d}';g=next(x for x in read('active-groups.json') if x['id']==name)
 status=read(f'results/terminal-{k:03d}.json');assert status['status']['state']=='FAILED' and '50001' in json.dumps(status)
 listing=subprocess.check_output([G,'storage','ls',f'gs://{BUCKET}/density36/{name}/'],text=True).splitlines()
 folder=R/'data/interrupted'/name;folder.mkdir(exist_ok=True)
 completed=[]
 for c in g['cases']:
  uri=f'gs://{BUCKET}/density36/{name}/{c}'
  if uri+'.summary.json' not in listing:continue
  download_summary(uri+'.summary.json',folder/(c+'.json'));s=json.loads((folder/(c+'.json')).read_text())
  assert s['result']['full_horizon'] and s['resume']['passed'] and s['checkpoint_manifest']['files']
  assert s['deck_sha256']==read('results/input-freeze.json')['cases'][c] and s['result']['binary_sha256']=='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
  meta=gc('storage','objects','describe',uri+'.tar.gz');assert int(meta['size'])==s['raw_bytes'];(folder/(c+'-raw-object.json')).write_text(json.dumps(meta,indent=2)+'\n');completed.append(c)
 cleanup={key:gc(*args,'--filter=labels.trial_id='+name) for key,args in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()};assert not any(cleanup.values())
 extra=[u for u in listing if any(w in u.lower() for w in ('partial','restart','checkpoint','failure'))]
 report={'group':name,'cleanup_verified':True,'cleanup':cleanup,'complete_cases':completed,'remaining_cases':[c for c in g['cases'] if c not in completed],'other_recovery_objects':extra,'listing':listing,'current_case_checkpoint_uploaded':bool(extra),'reason':'Spot preemption50001; no solver failure inferred'}
 (R/'results'/f'preemption-{k:03d}.json').write_text(json.dumps(report,indent=2)+'\n');print(name,'complete',len(completed),'remaining',len(report['remaining_cases']),'extras',extra,flush=True)
