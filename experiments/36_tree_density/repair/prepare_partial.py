"""Prepare only unfinished cases after verified preemption; never submit."""
from pathlib import Path
import json,lzma,hashlib,copy
R=Path(__file__).resolve().parent.parent
p=json.loads((R/'results/preemption-032.json').read_text());assert p['cleanup_verified'] and not p['current_case_checkpoint_uploaded']
g=next(x for x in json.loads((R/'active-groups.json').read_text()) if x['id']==p['group'])
blob=(R/g.get('package_file','data/packages/'+g['id']+'.xz')).read_bytes();assert hashlib.sha256(blob).hexdigest()==g['package_sha256']
old=json.loads(lzma.decompress(blob));new=copy.deepcopy(old);n=g['id']+'-r1';cases=p['remaining_cases'];assert not set(cases)&set(p['complete_cases'])
cfg=json.loads(new['group.json']);cfg['id']=n;cfg['cases']=cases;new['group.json']=json.dumps(cfg)
new['cases.json']=json.dumps([c for c in json.loads(new['cases.json']) if c['case'] in cases])
freeze=json.loads(new['input-freeze.json']);freeze['cases']={c:v for c,v in freeze['cases'].items() if c in cases};new['input-freeze.json']=json.dumps(freeze)
for c in p['complete_cases']:new.pop('decks/'+c+'.fds')
assert len(json.loads(new['cases.json']))==9
for key in ['runner.py','worker.py','transport.py']+[f'decks/{c}.fds' for c in cases]:assert new[key]==old[key]
out=R/'data/partial-recovery';out.mkdir(exist_ok=True);data=lzma.compress(json.dumps(new).encode(),preset=6);(out/(n+'.xz')).write_bytes(data)
(R/'results/partial-recovery-plan.json').write_text(json.dumps({'original_group':g['id'],'new_group':n,'cases':cases,'reused_completed_cases':p['complete_cases'],'package_sha256':hashlib.sha256(data).hexdigest(),'scientific_code_and_remaining_decks_unchanged':True,'proposed_allowance_usd':.4,'activated':False,'launch_after_capacity_available':True},indent=2)+'\n')
