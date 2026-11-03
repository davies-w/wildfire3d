"""Prepare only the interrupted baseline from the audited pilot06 checkpoint; offline."""
from cloud48_07 import *
import lzma
assert not (P/'submission-intent.json').exists()
old=R/'private06';assert json.loads((old/'closed.json').read_text())['passed']
a=json.loads((old/'terminal-archive.json').read_text());assert a['passed'] and not any(a['empty'].values())
objects={x['name']:x for x in a['objects']}
name='tree48_000997_baseline';prefix='tree48/pilot06/bulk/'+name+'/checkpoints/026/'
proof=next(x for x in json.loads((old/'worker-proofs.json').read_text()) if x['name']==prefix+'verified.json')
assert proof['sha256']==objects[proof['name']]['sha256']
cp=proof['proof'];assert cp['step']==5805 and cp['physical_time']==94.67241
payload=json.loads(lzma.decompress((R/'data/cloud05/input.xz').read_bytes()))
c=next(x for x in json.loads(payload['groups.json'])['bulk'] if x['pilot_case']==name)
assert cp['deck_sha256']==c['deck_sha256'] and any(x['name'].endswith('.restart') for x in cp['files'])
parts=[x for n,x in sorted(objects.items()) if n.startswith(prefix) and n.endswith('.part')];assert len(parts)==3
case=dict(case=c,saved_step=cp['step'],saved_time_s=cp['physical_time'],checkpoint_files=cp['files'],archive_parts=parts,archive_manifest=objects[prefix+'archive-manifest.json'],target_time_s=180)
save('recovery-plan.json',dict(cases=[case],completed_cases_excluded=True,fine_cases_excluded=True,original_decks_unchanged=True))
print(name,cp['step'],cp['physical_time'])
