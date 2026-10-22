"""Compare selected model checkpoint, separately fitted additive model and ablation on local validation."""
import copy,hashlib,json,sys,time
import numpy as np
from scene import ROOT
import component_hot_state_model as hot
from component_occlusion import apply
from evaluate_recursive_canopy_energy_budget import rollout
from component_additive_baseline import rollout as additive_rollout
from component_metrics import metrics

def main():
 model_path=ROOT/sys.argv[1];tag=sys.argv[2];model=json.loads(model_path.read_text());base=json.loads((ROOT/'data/additive_baseline.json').read_text());manifest=json.loads((ROOT/'component-development.json').read_text());names=[c['case'] for c in manifest['cases'] if c['split']=='validation' and (ROOT/'results'/f"{c['case']}-audit.json").exists()];rows=[]
 for name in names:
  raw=json.loads((ROOT/'data/component_states'/f'{name}.json').read_text());c=hot.series(raw)
  for label in ['graph','baseline','ablation']:
   start=time.perf_counter();g=copy.deepcopy(c['g'])
   if model.get('occlusion',False):g=apply(g,raw['configuration'])
   if label=='ablation':
    for i,n in enumerate(g['nodes']):
     if n['kind']=='vegetation':g['kernel'][i,:]=0
   pred=additive_rollout(base,g) if label=='baseline' else rollout(model,g);elapsed=time.perf_counter()-start;metric=metrics(c,pred,g);canopies=[]
   for i,n in enumerate(g['nodes']):
    if n['kind']=='vegetation':canopies.append(dict(id=n['id'],initialized=n['initialized'],fuel_kg_predicted=float(np.trapezoid(pred['state'][:,i,3],pred['time'])/17425),fuel_kg_reference=float(np.trapezoid(c['state'][:,i,3],c['time'])/17425)))
   rows.append(dict(case=name,model=label,metrics=metric,canopies=canopies,wall_seconds=elapsed));print(name,label,'ignition',metric['predicted_ignition_s'],'ref',metric['reference_ignition_s'],'T MAE',round(metric['temperature_MAE_all_C'],2),'dose median',metric['median_exposed_normalized_dose_error'],flush=True)
 (ROOT/'results'/f'local-candidate-comparison-{tag}.json').write_text(json.dumps(dict(model_path=str(model_path.relative_to(ROOT)),model_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256((ROOT/'data/additive_baseline.json').read_bytes()).hexdigest(),results=rows,scope='Local validation used for model selection; not untouched Stage C testing. Baseline fitted separately on single-canopy cases; ablation uses graph weights. All failed checks remain reported.'),indent=2))
if __name__=='__main__':main()
