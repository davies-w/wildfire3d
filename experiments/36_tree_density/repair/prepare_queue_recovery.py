"""Prepare, but do not activate or submit, replacements for proven queue timeouts."""
from pathlib import Path
import json,lzma,hashlib,copy,yaml
R=Path(__file__).resolve().parent.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
groups=json.loads((R/'restored-groups.json').read_text());out=[];replacements=[]
for old in groups:
 if old['id'] not in [f'x36-density-{i:03d}' for i in range(9,21)]:out.append(old);continue
 n=old['id'];proof=json.loads((R/'jobs'/n/'terminal-no-results.json').read_text());assert proof['run_duration_s']==0 and proof['cleanup_verified'] and proof['grant_removed']
 g=copy.deepcopy(old);new=n+'-r1';g['id']=new
 payload=json.loads(lzma.decompress((R/old.get('package_file','data/packages/'+n+'.xz')).read_bytes()));grp=json.loads(payload['group.json']);grp['id']=new;payload['group.json']=json.dumps(grp);blob=lzma.compress(json.dumps(payload).encode(),preset=6)
 p=R/'data/queue-recovery-packages'/(new+'.xz');p.parent.mkdir(exist_ok=True);p.write_bytes(blob);g['package_file']=str(p.relative_to(R));g['package_sha256']=sha(blob)
 folder=R/'jobs'/new;folder.mkdir(exist_ok=True);assert not (folder/'execution.json').exists()
 text=(R/'jobs'/n/old['workflow_file']).read_text().replace(n,new).replace(old['package_sha256'],g['package_sha256']);w=yaml.safe_load(text);assert w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['maxRetryCount']==0
 p=folder/'workflow-r1.yaml';p.write_text(text);g['workflow_sha256']=sha(p.read_bytes());(folder/'group-r1.json').write_text(json.dumps(g,indent=2)+'\n');out.append(g);replacements.append({'old':n,'new':new,'cases':g['cases']})
assert len(replacements)==12 and sum(len(x['cases']) for x in replacements)==144
(R/'proposed-queue-recovery-groups.json').write_text(json.dumps(out,indent=2)+'\n')
(R/'results/queue-recovery-plan.json').write_text(json.dumps(dict(activated=False,new_compute_launched=False,replacements=replacements,maximum_allowance_usd=4.8,existing_eight_jobs_unchanged=True,scientific_decks_unchanged=True,requires_user_approval=True),indent=2)+'\n')
