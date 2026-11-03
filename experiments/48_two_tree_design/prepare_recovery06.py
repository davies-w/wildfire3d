"""Prepare six non-fine continuation descriptions from verified saved checkpoints; no cloud mutation."""
from cloud48_05 import *
import lzma,re
Q=R/'private06';Q.mkdir(exist_ok=True)
assert not (Q/'submission-intent.json').exists()
assert json.loads((P/'closed.json').read_text())['passed']
archive=json.loads((P/'terminal-archive.json').read_text());assert archive['passed']
objects={v['name']:v for v in archive['objects']}
payload=json.loads(lzma.decompress((R/'data/cloud05/input.xz').read_bytes()));cases={c['pilot_case']:c for c in json.loads(payload['groups.json'])['bulk']}
expected={'tree48_000181_baseline','tree48_000997_baseline','tree48_001186_baseline','tree48_001991_baseline','tree48_000830_expanded','tree48_001824_expanded'}
result=[]
for name in sorted(expected):
 folder=P/'checkpoint-inspection'/name;proof=json.loads((folder/'proof.json').read_text());assert proof['all_parts_hash_verified']
 cp=json.loads((folder/'checkpoint.json').read_text());assert cp['deck_sha256']==cases[name]['deck_sha256']
 restarts=[x for x in cp['files'] if x['name'].endswith('.restart')];assert restarts
 text=(folder/(name+'.out')).read_text();steps=re.findall(r'Time Step\s+(\d+).*?Total Time:\s+([\d.Ee+-]+)',text,re.S);assert steps
 step,t=int(steps[-1][0]),float(steps[-1][1]);assert 0<t<180 and 'FDS stopped by user' in text
 prefix=proof['manifest'].rsplit('/',1)[0]+'/'
 parts=[v for n,v in sorted(objects.items()) if n.startswith(prefix) and n.endswith('.part')];assert parts
 result.append(dict(case=cases[name],saved_step=step,saved_time_s=t,last_device_time_s=proof['physical_time_last_device_s'],checkpoint_files=cp['files'],archive_parts=parts,archive_manifest=objects[proof['manifest']],target_time_s=180))
(Q/'recovery-plan.json').write_text(json.dumps(dict(cases=result,completed_cases_excluded=True,fine_cases_excluded=True,original_decks_unchanged=True),indent=2))
for x in result:print(x['case']['pilot_case'],x['saved_step'],x['saved_time_s'])
