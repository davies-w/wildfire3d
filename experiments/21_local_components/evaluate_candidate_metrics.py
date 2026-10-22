import copy,json
from scene import ROOT
import component_hot_state_model as hot
from evaluate_recursive_canopy_energy_budget import rollout
from component_metrics import metrics
model=json.loads((ROOT/'data/recursive_canopy_constrained/epoch300.json').read_text());rows=[]
for name in ['b21_single_validation','b21_transfer_validation']:
 c=hot.series(json.loads((ROOT/'data/component_states'/f'{name}.json').read_text()))
 for baseline in [False,True]:
  g=copy.deepcopy(c['g'])
  if baseline:
   # Independent-crown/additive baseline: crowns receive no messages from other
   # components; artificial initialization and local self-emission remain.
   for i,n in enumerate(g['nodes']):
    if n['kind']=='vegetation':g['kernel'][i,:]=0
  r=rollout(model,g);rows.append(dict(case=name,baseline=baseline,metrics=metrics(c,r,g)))
(ROOT/'results/recursive300-dose-validation.json').write_text(json.dumps(dict(scope='Two local development-validation configurations, not Stage C. Baseline is an explicit message ablation using the same fitted local rule; it is not separately trained.',results=rows),indent=2))
for r in rows:print(r['case'],r['baseline'],{k:v for k,v in r['metrics'].items() if k!='per_patch'})
