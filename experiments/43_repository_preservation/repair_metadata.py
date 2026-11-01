"""Retain scientific file references while continuing to redact spending values."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent;ROOT=R.parents[1];D=R/'data/public'
assert (R/'results/privacy-reviewed.json').exists()
ns={'__file__':str(R/'audit.py')};exec((R/'audit.py').read_text().split('paths=[]')[0],ns)
m=json.loads((D/'manifest.json').read_text());replace=[v for v in m['files'] if v['mode']=='financial/credential fields removed' and v['path'].endswith('.json') and (ROOT/v['path']).is_file()]
paths={v['path'] for v in replace};ns['rows']=[v for v in m['files'] if v['path'] not in paths];ns['exclusions']=m['excluded']
for row in replace:ns['process'](ROOT/row['path'],row['path'])
rows=sorted(ns['rows'],key=lambda x:x['path']);m.update(files=rows,excluded=ns['exclusions'],exported_files=len(rows),logical_bytes=sum(v['bytes'] for v in rows),unique_objects=len({v['md5'] for v in rows}))
assert len({v['path'] for v in rows})==len(rows)
# Scientific source hashes survive; nested spending/credential values do not.
assert ns['redact']({'files':{'energy_budget.py':'abc'},'estimated_spend_usd':3,'private_key':'example'})=={'files':{'energy_budget.py':'abc'}}
p=D/'experiments/21_local_components/results/component-test-prediction-freeze.json';x=json.loads(p.read_text());original=json.loads((ROOT/'experiments/21_local_components/results/component-test-prediction-freeze.json').read_text())
def contains(x,key):
 if isinstance(x,dict):return key in x or any(contains(v,key) for v in x.values())
 if isinstance(x,list):return any(contains(v,key) for v in x)
 return False
key='data/component_frozen/evaluate_recursive_canopy_energy_budget.py';assert contains(original,key) and contains(x,key)
(D/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(R/'results/scientific-field-review.json').write_text(json.dumps({'passed':True,'scientific_source_reference_restored':key,'json_records_rechecked':len(replace),'nested_spending_and_credentials_still_excluded':True},indent=2)+'\n')
print('Scientific references preserved; rechecked JSON records:',len(replace),flush=True)
