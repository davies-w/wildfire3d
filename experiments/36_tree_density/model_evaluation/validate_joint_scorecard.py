"""Inference-only comparison with the existing canonical worker evaluator."""
from pathlib import Path
import ast,json,hashlib,sys
import numpy as np
import torch
from joint_predictor import FrozenJointPredictor
from joint_scorecard import horizon_scorecard
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';sys.path.insert(0,str(S));from model import Transition
torch.set_num_threads(4);meta=json.loads((S/'schema.json').read_text());candidate=json.loads((R/'data/joint-decoder-candidate/candidate-plan.json').read_text());a=np.load(R/'data/joint-decoder-candidate/features.npz');ids=a['source_ids'][candidate['fit_indices'][:3]];a=np.load(S/'data/sequences.npz');raw=torch.tensor(a['state'][ids]);times=torch.tensor(a['time'][ids]);geometry=torch.tensor(a['geometry'][ids]);configuration=torch.tensor(a['configuration'][ids]);labels=torch.tensor(a['activity_labels'][ids]);ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geometry[:,None].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);mean,std=ck['mean'],ck['std'];z=(torch.asinh(raw/scale)-mean)/std
source=R/'data/pair-sequence/rotation0/worker.py';names={'horizon_metrics','history_at','advance','prefix_memory','mean_groups','phase_mae'};nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];ns=dict(torch=torch,np=np,P=dict(evaluation_horizons=[1,4,8,16,45],save_forecasts=False),device='cpu',raw=raw,times=times,external=external,config=configuration,active=torch.zeros(3,90,dtype=torch.bool),activity_labels=labels,scale=scale);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
reference=ns['horizon_metrics'](model,z,torch.arange(3),mean,std);predictor=FrozenJointPredictor(model,mean,std,scale,torch.tensor(meta['external_scales']));actual,_=horizon_scorecard(predictor,raw,geometry,times,configuration,labels)
for h,v in actual.items():
 for field in ['model_MAE','no_change_MAE','mean_absolute_truth']:assert np.allclose(v[field],reference[h][field],rtol=.002,atol=1e-6),(h,field)
 for phase in ['active','quiet','weak','transition']:
  for new,old in [('model_MAE','model_windows'),('no_change_MAE','no_change_windows'),('mean_absolute_truth','truth_windows')]:
   a,b=v['phases'][phase][new],reference[h][old]['v1_'+phase];assert (a is None and b is None) or np.allclose(a,b,rtol=.002,atol=1e-6),(h,phase,new)
proof=dict(passed=True,optimizer_updates=0,fit_histories=3,canonical_worker_reference_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),horizons_steps=[1,4,8,16,45],all_origin_overall_and_four_phase_metrics_replayed=True,source_sha256=hashlib.sha256((R/'model_evaluation/joint_scorecard.py').read_bytes()).hexdigest(),scope='CPU frozen baseline reference only. No confirmation/test evaluation, model selection, fitted-decoder score or accuracy improvement. Nominal16second headline is8steps; actual saved durations retained.')
(R/'results/joint-scorecard-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
