"""Pin interrupted case checkpoint for unique04 recovery, without running FDS."""
from cloud04 import *
import lzma
assert not (P/'submission-intent.json').exists()
old=R/'private03';assert json.loads((old/'closed.json').read_text())['passed']
a=json.loads((old/'terminal-archive.json').read_text());assert a['passed'] and not any(a['empty'].values())
objects={x['name']:x for x in a['objects']};name='tree51_000136_baseline';prefix='tree51/campaign03/wave-008/'+name+'/checkpoints/000/'
proof=next(x for x in json.loads((old/'worker-proofs.json').read_text()) if x['name']==prefix+'verified.json');assert proof['sha256']==objects[proof['name']]['sha256']
cp=proof['proof'];assert cp['step']==1800 and cp['physical_time']==121.56627
inner=json.loads((old/'checkpoint-inner-verification.json').read_text());assert inner['passed'] and inner['step']==cp['step']
payload=json.loads(lzma.decompress((R/'data/cloud03/wave-008.xz').read_bytes()));c=next(x for x in json.loads(payload['groups.json'])['wave'] if x['pilot_case']==name)
assert cp['deck_sha256']==c['deck_sha256'] and any(x['name'].endswith('.restart') for x in cp['files'])
parts=[x for n,x in sorted(objects.items()) if n.startswith(prefix) and n.endswith('.part')];assert len(parts)==1
save('recovery-plan.json',dict(cases=[dict(case=c,saved_step=cp['step'],saved_time_s=cp['physical_time'],checkpoint_files=cp['files'],archive_parts=parts,archive_manifest=objects[prefix+'archive-manifest.json'],target_time_s=180)],completed_cases_excluded=True,original_deck_unchanged=True,cloud_restore_not_yet_tested=True))
print('Pinned checkpoint-only recovery',name,cp['physical_time'])
