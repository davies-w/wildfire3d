"""Independent endpoint/origin/normalization checks for canonical features; no optimizer."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
from joint_predictor import FrozenJointPredictor
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';C=R/'data/joint-decoder-candidate';D=R/'data/canonical-feature-cache'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
proof=json.loads((R/'results/canonical-feature-cache-prepared.json').read_text());assert proof['prepared'] and proof['optimizer_updates']==0
for name,info in proof['files'].items():assert sha(D/name)==info['sha256'] and (D/name).stat().st_size==info['bytes']
for name,digest in proof['source_sha256'].items():assert sha(R/name)==digest
plan=json.loads((C/'candidate-plan.json').read_text());schema=json.loads((S/'schema.json').read_text());ids=np.load(D/'source-ids.npy');assert len(ids)==1872 and not set(ids.tolist())&set(schema['rotations'][0]['test']);length=np.load(D/'lengths.npy');offset=np.load(D/'offsets.npy');assert np.array_equal(length,np.minimum(45,90-np.arange(90))) and np.array_equal(offset,np.r_[0,length.cumsum()])
x=np.load(D/'features.npy',mmap_mode='r');b=np.load(D/'base-states.npy',mmap_mode='r');assert x.shape==(1872,3060,46) and b.shape==(1872,3060,4)
torch.set_num_threads(4);source=np.load(S/'data/sequences.npz');rows=np.array([plan['fit_indices'][0],plan['fit_indices'][100],plan['fit_indices'][-1]]);selected=ids[rows];raw=torch.tensor(source['state'][selected]);times=torch.tensor(source['time'][selected]);geometry=torch.tensor(source['geometry'][selected]);ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);sys.path.insert(0,str(S));from model import Transition
model=Transition('gated');model.load_state_dict(ck['model']);predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],torch.tensor(schema['physical_encoding_scales']),torch.tensor(schema['external_scales']));replays=[]
with torch.inference_mode():
 for h in [1,4,8,16,45]:
  for origin in sorted(set([0,(90-h)//2,90-h])):
   _,actual,actual_base=predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+h+1],h,return_features=True);cached=np.array(x[rows,offset[origin]:offset[origin]+h]);cached_base=np.array(b[rows,offset[origin]:offset[origin]+h]);assert np.allclose(actual.numpy(),cached,rtol=1e-4,atol=1e-4);assert np.allclose(actual_base.numpy(),cached_base,rtol=1e-4,atol=np.array([.0001,.0002,.00002,.001]));replays.append(dict(steps=h,origin=origin,observed_frames=origin+1,max_feature_error=float(np.abs(actual.numpy()-cached).max()),max_state_error=np.abs(actual_base.numpy()-cached_base).max((0,1)).tolist()))
normalization=json.loads((D/'fit-normalization.json').read_text());audit=json.loads((R/'results/guard-matched-fit-horizons.json').read_text());assert audit['fit_histories']==1332 and audit['confirmation_and_test_not_evaluated'];norm_checks={}
for h in [1,4,8,16,45]:
 old=np.array(audit['baseline'][str(h)]['model_MAE']);new=np.array(normalization[str(h)]['physical_MAE']);assert np.allclose(old,new,rtol=.001,atol=1e-8);assert normalization[str(h)]['origins_per_history']==91-h;norm_checks[str(h)]=dict(independent_baseline_MAE=old.tolist(),cached_fit_MAE=new.tolist(),relative_error=(np.abs(new-old)/old).tolist())
assert all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items())
out=dict(passed=True,optimizer_updates=0,original_test_excluded=True,role_order_verified=True,all_file_hashes_verified=True,all_valid_origins_per_horizon={str(h):91-h for h in [1,4,8,16,45]},fresh_observed_prefix_replays=replays,fit_normalization_matches_independent_all_origin_scorecard=norm_checks,normalization_uses_fit_only=True,source_sha256=sha(Path(__file__)),scope='Cache/inference validation only. Fresh fit-only forecasts include first/middle/last valid origin for each window, including late origins75to89 absent from oldrolling16cache. Independent full-fit canonical scorecard validates endpoint targets, origin counts and weighting. No fitted update, new holdout score, accuracy improvement or deployment claim.')
(R/'results/canonical-feature-cache-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['fresh_observed_prefix_replays','fit_normalization_matches_independent_all_origin_scorecard']},indent=2))
