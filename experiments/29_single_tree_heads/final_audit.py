import json,hashlib,time
from original_cnn import ROOT
from pathlib import Path
p=ROOT.parent/'28_single_tree_repair';f=json.loads((p/'results/prediction-freeze.json').read_text());assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==h for n,h in f['files'].items())
cs=json.loads((ROOT/'cases.json').read_text());expected={c['case'] for c in cs};assert len(expected)==38
rows={}
for n in ['previous','bound_only','bounded','strength_only','heads','interpolation']:
 r=json.loads((ROOT/f'results/{n}-evaluation.json').read_text());observed={x['case'] for x in r['rows']};want={c['case'] for c in cs if c['split']=='validation'} if n=='interpolation' else expected;assert observed==want
 assert all(len(h['time_s'])==91 for h in r['histories'])
 if n in ['bound_only','bounded','strength_only','heads']:assert all(x['all']['minimum_C']>=5.999 for x in r['rows'])
 rows[n]=dict(configurations=len(observed),frames_per_configuration=91)
files=[* (ROOT/'data/models').glob('*.pt'),ROOT/'models.py',ROOT/'train.py',ROOT/'evaluate.py',ROOT/'cases.json',ROOT/'results/temperature-bound.json']
result=dict(created_unix=time.time(),parent_freeze_verified=True,development_only=True,no_new_FDS_runs=True,models=rows,files={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},note='Development snapshot only; not a fresh-test prediction freeze. Both old test datasets excluded from fitting and evaluation.')
(ROOT/'results/final-audit.json').write_text(json.dumps(result,indent=2));print('All complete histories verified; development only; parent freeze intact')
