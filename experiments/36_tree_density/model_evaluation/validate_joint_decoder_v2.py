"""TRAIN-only representation/invariant checks; no optimizer or fitted decoder."""
from pathlib import Path
import json,hashlib
import numpy as np
import torch
from joint_decoder_v2 import JointDecoder,interval_mass_loss_rates
R=Path(__file__).resolve().parents[1];D=R/'data/gas-head-candidate'
decoder_hash=hashlib.sha256((R/'model_evaluation/joint_decoder_v2.py').read_bytes()).hexdigest();validator_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(R/'results/joint-decoder-v2-preflight.json').write_text(json.dumps(dict(passed=False,status='running',decoder_sha256=decoder_hash,validator_sha256=validator_hash))+'\n')
a=np.load(D/'features.npz');p=json.loads((D/'candidate-plan.json').read_text());n=json.loads((D/'base-normalization.json').read_text());ids=p['train_indices'];torch.set_num_threads(4);torch.manual_seed(3620)
x=torch.tensor(a['features'][ids]);base=torch.tensor(a['base_states'][ids]);raw=torch.tensor(a['truth'][ids]);times=torch.tensor(a['time'][ids]);old=torch.load(D/'initial-head.pt',map_location='cpu',weights_only=False);std=torch.tensor(n['std']);scale=torch.tensor(n['physical_encoding_scales']);args=(old['feature_mean'],old['feature_std'],std,scale)
initials={};reports={}
for mode in ['direct','interval']:
 torch.manual_seed(3620);m=JointDecoder(*args,mode);initials[mode]={k:v.detach().clone() for k,v in m.state_dict().items()}
 with torch.inference_mode():
  out=m(x,base,raw[:,0],times);assert torch.isfinite(out).all()
  if mode=='direct':assert torch.equal(out,base)
  else:
   assert (out[:,:,:2]>=0).all() and (out[:,:,:2]<=raw[:,0,None,:2]+1e-5).all();rate=interval_mass_loss_rates(out,raw[:,0],times);assert (rate>=-1e-6).all();assert (out[:,:,2]>=0).all();assert torch.equal(out[:,:,3],base[:,:,3])
  assert torch.allclose(m(x[:1],base[:1],raw[:1,0],times[:1]),out[:1],rtol=1e-5,atol=1e-6)
  physical_change=(out-base).abs().amax((0,1)).tolist()
 # Only isolated derivatives at initialization; parameters never updated.
 pred=m(x[:64],base[:64],raw[:64,0],times[:64]);loss=((torch.asinh(pred/scale)-torch.asinh(raw[:64,1:]/scale))/std).square().mean();loss.backward();assert all(v.grad is not None and torch.isfinite(v.grad).all() for v in m.parameters());perhead=m.w2.grad.norm(dim=1);assert (perhead>0).all();assert all(torch.equal(v,initials[mode][k]) for k,v in m.state_dict().items())
 reports[mode]=dict(parameters=sum(v.numel() for v in m.parameters()),initial_max_physical_change_from_GRU=physical_change,isolated_last_layer_gradient_norm_per_head=perhead.tolist(),state_unchanged=True)
assert all(torch.equal(initials['direct'][k],initials['interval'][k]) for k in initials['direct'])
# A flat base must have a usable derivative for a new interval loss.
flat=base[:1].clone();initial=raw[:1,0].clone();flat[:,:,:2]=initial[:,None,:2];probe=JointDecoder(*args,'interval');probe.load_state_dict(initials['interval']);out=probe(x[:1],flat,initial,times[:1]);target=initial[:,1]*.5;flat_loss=(out[:,-1,1]-target).square().mean();flat_loss.backward();assert probe.w2.grad[1].norm()>1e-4
flat[:,:,2]=-.001;probe=JointDecoder(*args,'interval');probe.load_state_dict(initials['interval']);out=probe(x[:1],flat,initial,times[:1]);assert torch.equal(out[:,:,2],torch.zeros_like(out[:,:,2]));gas_loss=(out[:,:,2]-.01).square().mean();gas_loss.backward();assert probe.w2.grad[2].norm()>1e-7

# Arbitrarily initialized probe checks prefix causality, not fitted accuracy.
for mode in ['direct','interval']:
 probe=JointDecoder(*args,mode);torch.nn.init.normal_(probe.w2,std=.05);torch.nn.init.normal_(probe.b2,std=.05)
 with torch.inference_mode():
  full=probe(x[:8],base[:8],raw[:8,0],times[:8]);prefix=probe(x[:8,:16],base[:8,:16],raw[:8,0],times[:8,:17]);assert torch.allclose(full[:,:16],prefix,rtol=1e-5,atol=1e-6)
  if mode=='interval':
   initial=raw[:1,0].clone();initial[:,0]=-.001;decoded=probe(x[:1],base[:1],initial,times[:1]);assert torch.equal(decoded[:,:,0],torch.zeros_like(decoded[:,:,0]));assert torch.isfinite(decoded).all();assert (interval_mass_loss_rates(decoded,initial,times[:1],project_initial=True)>=-1e-6).all()

# Oracle representation check uses true masses only to quantify the decoder's floor.
initial=raw[:,0,:2].double();target=raw[:,1:,:2].double();floor=initial[:,None].clamp_min(1e-12)*1e-6;projected=torch.maximum(torch.minimum(target,initial[:,None]),floor);previous=torch.cat([initial[:,None].clamp_min(1e-12),projected[:,:-1]],1);oracle=initial[:,None]*torch.exp(-torch.cumsum((previous.log()-projected.log()).clamp_min(0),1));error=(oracle-target).abs();oracle_report=dict(mean_absolute_error_kg=error.mean((0,1)).tolist(),maximum_error_kg=error.amax((0,1)).tolist())
out=dict(decoder_sha256=decoder_hash,validator_sha256=validator_hash,flat_base_new_loss_gradient_nonzero=True,negative_base_new_gas_gradient_nonzero=True,prefix_invariant=True,negative_estimated_initial_water_projection_checked=True,passed=True,train_only=True,histories=len(ids),optimizer_instantiated=False,optimizer_updates=0,matched_initial_parameter_bytes=True,modes=reports,oracle_interval_mass_representation=oracle_report,scope='Untrained decoder checks only. Direct head initially reproduces baseline exactly; interval head initially projects mass trajectories and clips negative gas, so it is NOT baseline-identical. Nonnegative nonincreasing mass is a modeling prior; tiny negative water labels are not exactly representable. Heating index negatives are preserved. Separate interval mass-loss rates and endpoint gas samples are not forced equal. Oracle uses truth and is not a usable forecast, learned improvement, attainable model error bound or physical validation. Frozen GRU dynamics/features remain unchanged; no validation/test outcomes or optimizer.')
(R/'results/joint-decoder-v2-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
