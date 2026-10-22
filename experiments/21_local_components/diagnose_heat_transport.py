"""Spatial heat-model diagnosis using local validation only; not inference."""
import json,numpy as np
from scene import ROOT
import component_model as m
import component_heat_rule as hr
from diagnose_wall_response import response
rows=[]
for name in ['b21_single_validation','b21_transfer_validation']:
 c=m.series(json.loads((ROOT/'data/component_states'/f'{name}.json').read_text()));b=np.array([n['kind']=='building' for n in c['g']['nodes']]);truth=c['state'][:,b,0];j=np.argmax(truth.max(0));early=c['time']<=26
 model=json.loads((ROOT/'data/component_exchange_candidates/exchange_additive_sqrt_100.json').read_text());h=np.array([hr.predict(model,c['g'],s,t) for s,t in zip(c['state'],c['time'])]);temp=response(h[:,b],np.full(b.sum(),5.670374419e-11*293.15**4));r=m.rollout(model,c['g'],90);auto=r['heat'][:len(c['time']),b]
 rows.append(dict(case=name,selected_patch=c['g']['nodes'][np.flatnonzero(b)[j]],true_state_heating_thermal_peak_C=float(temp.max()),reference_peak_C=float(truth.max()),pre26_selected_true_mean_flux_kw_m2=c['heat'][early][:,b][:,j].mean(0).tolist(),pre26_selected_true_peak_flux_kw_m2=c['heat'][early][:,b][:,j].max(0).tolist(),pre26_selected_model_mean_given_true_states=h[early][:,b][:,j].mean(0).tolist(),pre26_selected_model_mean_autonomous=auto[early,j].mean(0).tolist()))
(ROOT/'results/component-heat-transport-diagnosis.json').write_text(json.dumps(dict(scope='True-state diagnostic is not autonomous inference. Fluxes in radiation,convection order. Patch selected by validation peak solely for diagnosis.',results=rows),indent=2));print(json.dumps(rows,indent=2))
