"""Prepare unchanged inputs for only unfinished cases in three diagnosed preemptions."""
import copy,hashlib,json,lzma
from pathlib import Path
R=Path(__file__).resolve().parent.parent
for k in (88,93,115):
 audit=json.loads((R/f'results/preemption-{k:03d}.json').read_text());assert audit['cleanup_verified'] and not audit['current_case_checkpoint_uploaded']
 g=next(x for x in json.loads((R/'active-groups.json').read_text()) if x['id']==audit['group']);name=g['id']+'-r1';cases=audit['remaining_cases'];assert cases and not set(cases)&set(audit['complete_cases'])
 blob=(R/g.get('package_file','data/packages/'+g['id']+'.xz')).read_bytes();assert hashlib.sha256(blob).hexdigest()==g['package_sha256'];old=json.loads(lzma.decompress(blob));new=copy.deepcopy(old)
 cfg=json.loads(new['group.json']);cfg.update(id=name,cases=cases);new['group.json']=json.dumps(cfg);new['cases.json']=json.dumps([c for c in json.loads(new['cases.json']) if c['case'] in cases]);freeze=json.loads(new['input-freeze.json']);freeze['cases']={c:v for c,v in freeze['cases'].items() if c in cases};new['input-freeze.json']=json.dumps(freeze)
 for c in audit['complete_cases']:new.pop('decks/'+c+'.fds')
 for key in ['runner.py','worker.py','transport.py']+[f'decks/{c}.fds' for c in cases]:assert new[key]==old[key]
 out=R/'data/late-recovery'/name;out.mkdir(parents=True,exist_ok=True);payload=lzma.compress(json.dumps(new).encode(),preset=6);package=out/'input.xz';package.write_bytes(payload);ph=hashlib.sha256(payload).hexdigest()
 source=(R/'jobs'/g['id']/g.get('workflow_file','workflow.yaml')).read_text();assert hashlib.sha256(source.encode()).hexdigest()==g['workflow_sha256'];wf=source.replace(g['id'],name).replace(g['package_sha256'],ph);assert wf.replace(name,g['id']).replace(ph,g['package_sha256'])==source;(out/'workflow.yaml').write_text(wf)
 proof={'group':name,'original_group':g['id'],'cases':cases,'excluded_completed_cases':audit['complete_cases'],'package_sha256':ph,'workflow_sha256':hashlib.sha256(wf.encode()).hexdigest(),'image_uri':g['image_uri'],'only_identity_and_package_hash_changed':True,'package_file':str(package.relative_to(R)),'workflow_file':str((out/'workflow.yaml').relative_to(R))}
 (out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');(R/'jobs'/name).mkdir(exist_ok=True);print(name,len(cases),flush=True)
