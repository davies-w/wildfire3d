"""Preserve one bounded group of proven completed cases; never submit cloud jobs."""
from cloud06 import *
import argparse,sys,shutil
parser=argparse.ArgumentParser();parser.add_argument('--group',required=True,type=int);parser.add_argument('--resume',action='store_true');args=parser.parse_args();assert 1<=args.group<=999
group=f'group{args.group:03d}';record=P/('collection-'+group+'.json');assert not record.exists() or args.resume,'Inspect prior group before any repeat';assert not (P/('preservation-'+group+'.json')).exists(),'Already preserved'
with (P/'preservation.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 proofs=json.loads((P/'worker-proofs.json').read_text());ids=[];size=0
 for x in proofs:
  if not x['name'].endswith('/completion.json') or not x['proof']['passed']:continue
  wave=x['name'].split('/')[-3]
  if (R/'data/completed06'/wave/'proof.json').exists():continue
  jobs=[v for v in proofs if v['name'].startswith(PREFIX+wave+'/job-status.json.') and v['proof'].get('status',{}).get('state')=='SUCCEEDED']
  if len(jobs)!=1:continue
  n=x['proof']['archive']['bytes']
  if len(ids)>=18 or size+n>=2*10**9:break
  ids.append(int(wave.split('-')[1]));size+=n
 if args.resume:
  prior=json.loads(record.read_text());ids=prior['indices'];size=prior['archive_bytes'];assert len(ids)<=18 and size<2*10**9
 assert ids and shutil.disk_usage(R).free>8*1024**3
 save(record.name,dict(indices=ids,max_cases=18,archive_bytes=size));print('Selected',ids,'archive_bytes',size,flush=True)
 for i in ids:subprocess.run([sys.executable,str(R/'collect_completed06.py'),'--wave',f'wave-{i:06d}'],check=True)
 stage='completed06_'+group;f=R/'dvc.yaml';s=f.read_text();assert '\n  '+stage+':' not in s
 s+='  '+stage+':\n    cmd:\n'+''.join(f'    - ../../.venv/bin/python collect_completed06.py --wave wave-{i:06d}\n' for i in ids)+'    frozen: true\n    outs:\n'+''.join(f'    - data/completed06/wave-{i:06d}\n' for i in ids);f.write_text(s)
 repo=R.parents[1];helper=repo/'scripts/dvc_hf.py';target=str(f.relative_to(repo))+':'+stage
 subprocess.run([sys.executable,str(helper),'commit',target],cwd=repo,check=True)
 state=repo/'experiments/43_repository_preservation/results/direct-hf';plan=json.loads((state/'plan.json').read_text());prefixes=[str((R/'data/completed06'/f'wave-{i:06d}').relative_to(repo))+'/' for i in ids]
 for o in plan['objects'].values():assert o.get('directory') or any(o['source'].startswith(v) for v in prefixes)
 dedicated=P/('scientific-plan-'+group+'.json');dedicated.write_bytes((state/'plan.json').read_bytes());print('Reviewed plan',len(plan['objects']),sha(dedicated),flush=True)
 subprocess.run([sys.executable,str(helper),'push','--plan',str(dedicated)],cwd=repo,check=True)
 v=json.loads((state/'upload-verification.json').read_text());assert v['passed'] and v['objects']==len(plan['objects']) and v['remote_size_and_xet_verified'] and v['directory_anonymous_readback'] and v['plan_sha256']==sha(dedicated)
 save('preservation-'+group+'.json',v);print('PRESERVATION PASS',group,len(ids),flush=True)
