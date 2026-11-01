"""Replay one representative gas dip per gallery as an uninterrupted forecast; no fitting."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];load=lambda p:json.loads(p.read_text());audit=load(R/'results/gallery-forecast-provenance.json');torch.set_num_threads(4);reports={}
for name,S,outputs,model_file,kind in [('old_gated',R.parent/'35_surrogate_diagnostics/attempt24',R.parent/'35_surrogate_diagnostics/attempt24/data/collected','model.py','gated'),('denser',R/'data/model-training',R/'data/model-training-results','model.py','control'),('stride_pair',R/'data/pair-sequence/rotation0',R/'data/pair-sequence-r0-results','gated_model.py','gated')]:
 e=audit['galleries'][name]['representative_examples']['3:2'];case=int(e['source_id']);fold=e['fold'];checkpoint=outputs/f'fold{fold:02}-selected.pt';ck=torch.load(checkpoint,map_location='cpu',weights_only=False);spec=importlib.util.spec_from_file_location('dip_'+name,S/model_file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);m=module.Transition(kind);m.load_state_dict(ck['model']);m.eval();before={k:v.clone() for k,v in m.state_dict().items()}
 schema=load(S/'schema.json');a=np.load(S/'data/sequences.npz');raw=torch.tensor(a['state'][case]);times=torch.tensor(a['time'][case]);geom=torch.tensor(a['geometry'][case]);scales=torch.tensor(schema['physical_encoding_scales']);mean=ck['mean'].cpu();std=ck['std'].cpu();z=(torch.asinh(raw/scales)-mean)/std;dt=times[1:]-times[:-1];on=(20-times[:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[None].expand(90,-1),on[:,None],dt[:,None]],-1)/torch.tensor(schema['external_scales'])
 def history_at(j):return z[(torch.arange(-3,1)+j).clamp_min(0)][None]
 @torch.no_grad()
 def forecast(origin,h):
  memory=None
  if origin:
   histories=torch.stack([history_at(j)[0] for j in range(origin)]);inputs=m.inputs(histories,external[:origin])[None];out,_=m.cell(inputs);memory=out[:,-1]
  history=history_at(origin);values=[]
  for j in range(origin,origin+h):
   p,memory=m.step(history,external[j:j+1],memory);values.append((torch.sinh(p[0]*std+mean)*scales).numpy());history=torch.cat([history[:,1:],p[:,None]],1)
  return np.array(values)
 origin=e['trace'][1]['origin_step'];target=e['trace'][1]['target_step'];fixed=forecast(origin,18);full=forecast(0,90);central=target-origin-1;gpu=e['trace'][1]['saved_endpoint_value'];assert np.isclose(fixed[central,2],gpu,rtol=.002,atol=.002),(name,fixed[central,2],gpu)
 traces=[]
 for point in e['trace']:
  t=point['target_step'];traces.append(dict(**point,same_origin_uninterrupted_gas=float(fixed[t-origin-1,2]),full_origin0_gas=float(full[t-1,2])))
 assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items());rebound=float(fixed[central+1,2]-fixed[central,2]);display_rebound=e['trace'][2]['plotted_value']-e['trace'][1]['plotted_value']
 reports[name]=dict(case=e['case'],page=e['local_page'],fixed_origin_step=origin,fixed_origin_time_s=e['trace'][1]['origin_time_s'],saved_16step_endpoint_replayed_close=True,trace=traces,display_gas_rebound=display_rebound,same_origin_gas_rebound=rebound,coherent_forecast_also_rebounds=rebound>0,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),model_source_sha256=hashlib.sha256((S/model_file).read_bytes()).hexdigest())
 print(name,e['case'],'display rebound',display_rebound,'uninterrupted rebound',rebound,json.dumps(traces),flush=True)
out=dict(passed=True,optimizer_updates=0,parameters_unchanged=True,cpu_threads=4,representative_published_examples=True,models_replayed=3,reports=reports,scope='Descriptive replay of existing published-model test scenarios to investigate plot semantics, not new correction fitting, model selection or pristine accuracy validation. Examples were chosen for local gas valleys and need not be the user\'s exact dip. Actual observation conditioning only through each stated origin; fixed-origin continuation receives no newer truth. GPU endpoint parity tolerance0.2%relative/0.002physical absolute, inherited original gallery check; numbers are not claimed bitwise CPU/CUDA equal. Both refreshed-origin revisions and within-forecast dynamics can contribute; construction alone cannot attribute an individual rebound.')
(R/'results/gallery-dip-replay.json').write_text(json.dumps(out,indent=2)+'\n')
