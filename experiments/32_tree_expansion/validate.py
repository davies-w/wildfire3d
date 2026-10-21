from pathlib import Path
import json,re,hashlib
R=Path(__file__).parent
cs=json.loads((R/'cases.json').read_text());f=json.loads((R/'results/input-freeze.json').read_text());assert len(cs)==472 and len({c['seed'] for c in cs})==472
assert hashlib.sha256((R/'cases.json').read_bytes()).hexdigest()==f['manifest_sha256'];groups={}
for c in cs:
 s=(R/'data/decks'/(c['case']+'.fds')).read_text();assert hashlib.sha256(s.encode()).hexdigest()==f['cases'][c['case']];assert len(re.findall(r'MOISTURE_CONTENT='+str(c['moisture'])+r'\b',s))==4;assert 'RND_SEED='+str(c['seed']) in s;assert 'IJK=48,32,32' in s
 normalized=re.sub(r"CHID='[^']+'","CHID='CASE'",s);normalized=re.sub(r'RND_SEED=\d+','RND_SEED=SEED',normalized);groups.setdefault(c['configuration'],[]).append((c,normalized))
assert len(groups)==432 and sum(len(v)==3 for v in groups.values())==20
for rows in groups.values():assert len({c['split'] for c,s in rows})==1 and len({s for c,s in rows})==1
out=dict(passed=True,new_runs=len(cs),new_unique_configurations=len(groups),three_seed_groups=20,all_seed_replicas_differ_only_in_seed_and_case_name=True,no_cross_split_configuration_overlap=True,all_deck_hashes_verified=True)
(R/'results/validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
