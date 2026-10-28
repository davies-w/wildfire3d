"""CPU inference-only prefix API replay; no future-state input or optimizer."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
from joint_predictor import FrozenJointPredictor
from joint_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';C=R/'data/joint-decoder-candidate';F=R/'data/joint-rolling-features';sys.path.insert(0,str(S));from model import Transition
torch.set_num_threads(4);plan=json.loads((C/'candidate-plan.json').read_text());a=np.load(C/'features.npz');ids=a['source_ids'][plan['fit_indices'][:8]];source=np.load(S/'data/sequences.npz');meta=json.loads((S/'schema.json').read_text());ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);scales=torch.tensor(meta['physical_encoding_scales']);predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],scales,torch.tensor(meta['external_scales']));rolling=np.load(F/'features.npy',mmap_mode='r');base=np.load(F/'base-states.npy',mmap_mode='r');rows=plan['fit_indices'][:8];raw=torch.tensor(source['state'][ids]);times=torch.tensor(source['time'][ids]);geom=torch.tensor(source['geometry'][ids]);reports=[]
for origin,steps in [(0,90),(0,16),(16,16),(74,16)]:
 prediction,features,states=predictor.forecast(raw[:,:origin+1],geom,times[:,:origin+steps+1],steps,return_features=True)
 ref=a['features'][rows] if steps==90 else rolling[rows,origin];rbase=a['base_states'][rows] if steps==90 else base[rows,origin]
 assert np.allclose(features,ref,rtol=1e-5,atol=3e-6) and np.allclose(states,rbase,rtol=1e-5,atol=3e-5)
 reports.append(dict(origin=origin,steps=steps,max_feature_absolute_error=float(np.abs(features.numpy()-ref).max()),max_state_absolute_error=float(np.abs(states.numpy()-rbase).max())))
initial=torch.load(C/'initial-decoder.pt',map_location='cpu',weights_only=False);norm=json.loads((C/'base-normalization.json').read_text())
for mode in ['direct','interval']:
 decoder=JointDecoder(initial['feature_mean'],initial['feature_std'],torch.tensor(norm['std']),scales,mode);decoder.load_state_dict(initial['model']);predictor.decoder=decoder
 with torch.inference_mode():
  prediction,features,states=predictor.forecast(raw[:,:17],geom,times[:,:33],16,return_features=True);expected=decoder(features,states,raw[:,16],times[:,16:33]);assert torch.equal(prediction,expected)
assert all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items())
proof=dict(passed=True,optimizer_updates=0,fit_histories_only=True,forecast_inputs='Observed prefix only, seven geometry parameters, known time grid and imposed20second ignition command. No future target state argument.',cached_full_and_rolling_features_replayed=reports,both_untrained_decoder_modes_replayed=True,base_state_unchanged=True,source_sha256=hashlib.sha256((R/'model_evaluation/joint_predictor.py').read_bytes()).hexdigest(),scope='Inference implementation verification only; no trained-decoder accuracy claim or deployment.')
(R/'results/joint-predictor-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
