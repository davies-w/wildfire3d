"""Evict one verified group's local solve files, retaining proofs and remote DVC data."""
from cloud07 import *
import argparse,yaml
p=argparse.ArgumentParser();p.add_argument('--group',type=int,required=True);p.add_argument('--apply',action='store_true');a=p.parse_args();assert 1<=a.group<=999
g=f'group{a.group:03d}';repo=R.parents[1]
with (P/'preservation.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 planpath=P/f'scientific-plan-{g}.json';plan=json.loads(planpath.read_text());receipt=json.loads((P/f'preservation-{g}.json').read_text())
 assert receipt['passed'] and receipt['remote_size_and_xet_verified'] and receipt['directory_anonymous_readback'] and receipt['plan_sha256']==sha(planpath) and receipt['objects']==len(plan['objects'])
 record=P/f'eviction-{g}.json';assert not record.exists(),'Already evicted; inspect receipt'
 ids=json.loads((P/f'collection-{g}.json').read_text())['indices'];assert 0<len(ids)<=18
 outs=yaml.safe_load((R/'dvc.lock').read_text())['stages']['completed07_'+g]['outs']
 assert {x['path'] for x in outs}=={f'data/completed07/wave-{i:06d}' for i in ids}
 assert all(x['md5'] in plan['objects'] and plan['objects'][x['md5']].get('directory') for x in outs)
 objects={v['source']:(k,v) for k,v in plan['objects'].items() if not v.get('directory')};files=[]
 for i in ids:
  wave=R/'data/completed07'/f'wave-{i:06d}';proof=json.loads((wave/'proof.json').read_text());assert proof['passed'] and len(proof['cases'])==1
  c=proof['cases'][0];assert c['passed'] and c['physical_time_s']>=180-1e-5 and c['archive_parts_verified']
  for entry in c['files']:
   f=wave/c['case']/entry['path'];assert f.is_relative_to(wave/c['case']/'solve') and not f.is_symlink() and f.resolve().is_relative_to(wave.resolve())
   key=str(f.relative_to(repo));md5,o=objects[key];assert f.stat().st_size==o['size']==entry['bytes'] and sha(f)==o['sha256']==entry['sha256']
   files.append(dict(path=key,bytes=o['size'],sha256=o['sha256'],md5=md5))
 total=sum(x['bytes'] for x in files);assert total<4*1024**3
 result=dict(passed=True,group=g,files=files,bytes=total,plan_sha256=sha(planpath),proofs_retained=True,remote_untouched=True,restoration='Use scripts/dvc_hf.py restore with scoped DVC output records; see docs/storage.md')
 print(g,len(files),total,'apply',a.apply,flush=True)
 if a.apply:
  save(f'eviction-intent-{g}.json',result)
  for x in files:(repo/x['path']).unlink()
  save(record.name,result)
