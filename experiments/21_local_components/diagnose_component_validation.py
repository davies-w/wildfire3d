"""Diagnostic decomposition on local validation; never an inference implementation."""
import json,numpy as np
from scene import ROOT
import component_model as m
raw=json.loads((ROOT/'data/component_states/b21_single_validation.json').read_text());c=m.series(raw);rows=[]
for name in ['additive_sqrt_10','interaction_sqrt_10']:
 model=json.loads((ROOT/'data/component_candidates'/f'{name}.json').read_text());roll=m.rollout(model,c['g'],90);st=c['state'];types=np.array([n['kind'] for n in c['g']['nodes']]);heat=[]
 for k,t in enumerate(c['time']):
  x=m.equilibrium_features(c['g'],st[k],t,model['interaction']);h=np.zeros_like(c['heat'][k])
  for kind,head in model['models'].items():
   mask=types==kind;h[mask]=np.sinh(np.clip(m.predict(head['heat'],x[mask]),-7,7))*10
  heat.append(h)
 h=np.array(heat);r=roll['state'][:len(st)];b=types=='building';v=types=='vegetation'
 rows.append(dict(candidate=name,diagnostic_uses_FDS_states=True,building_heat_mae_with_true_states_kw_m2=np.abs(h[:,b]-c['heat'][:,b]).mean((0,1)).tolist(),source_emitted_energy_reference_kJ=float(np.trapezoid(st[:,v,3].sum(1),c['time'])),source_emitted_energy_autonomous_kJ=float(np.trapezoid(r[:,v,3].sum(1),c['time'])),source_peak_time_reference_s=float(c['time'][np.argmax(st[:,v,3].sum(1))]),source_peak_time_autonomous_s=float(c['time'][np.argmax(r[:,v,3].sum(1))])))
(ROOT/'results/component-validation-diagnosis.json').write_text(json.dumps(dict(scope='True-state diagnostic only; production rollout remains autonomous. Incoming radiation and signed convection in that order.',results=rows),indent=2));print(json.dumps(rows,indent=2))
