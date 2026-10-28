"""Prepare all stride-one observed-prefix forecasts up to45steps; no optimizer or test forecasts."""
from pathlib import Path
import datetime,fcntl,hashlib,json,shutil,sys
import numpy as np
import torch
from joint_predictor import FrozenJointPredictor
from joint_metrics import groups
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';C=R/'data/joint-decoder-candidate';F=R/'data/joint-rolling-features';D=R/'data/canonical-feature-cache'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,v):
 t=p.with_suffix(p.suffix+'.new');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def main():
 assert shutil.disk_usage(R).free>12*1024**3
 D.mkdir(exist_ok=True)
 with (D/'prepare.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not (R/'results/canonical-feature-cache-prepared.json').exists(),'Completed cache is immutable; validate it instead'
  torch.set_num_threads(4);schema=json.loads((S/'schema.json').read_text());plan=json.loads((C/'candidate-plan.json').read_text());a=np.load(C/'features.npz');source=np.load(S/'data/sequences.npz');ids=a['source_ids'];rotation=schema['rotations'][0]
  assert len(ids)==1872 and not set(ids.tolist())&set(rotation['test']) and set(ids.tolist())==set(rotation['train']+rotation['validation'])
  sys.path.insert(0,str(S));from model import Transition
  ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);assert sha(S/'data/initial.pt')==plan['base_checkpoint_sha256'];model=Transition('gated');model.load_state_dict(ck['model']);before={k:v.clone() for k,v in model.state_dict().items()};predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],torch.tensor(schema['physical_encoding_scales']),torch.tensor(schema['external_scales']))
  raw=torch.tensor(source['state'][ids]);times=torch.tensor(source['time'][ids]);geometry=torch.tensor(source['geometry'][ids]);assert np.array_equal(raw.numpy(),a['truth']) and np.array_equal(times.numpy(),a['time'])
  lengths=np.minimum(45,90-np.arange(90));offsets=np.r_[0,lengths.cumsum()];assert offsets[-1]==3060
  provenance={str(p.relative_to(R)):sha(p) for p in [S/'data/initial.pt',S/'data/sequences.npz',C/'candidate-plan.json',C/'features.npz',R/'model_evaluation/joint_predictor.py',Path(__file__)]}
  diagnosis=json.loads((R/'results/canonical-cache-replay-diagnosis.json').read_text());assert diagnosis['worst_subset_small_batch_vs_original_reference_max']==0 and diagnosis['optimizer_updates']==0;assert diagnosis['max_feature_error_by_column'][36:]==[0.]*10
  provenance['results/canonical-cache-replay-diagnosis.json']=sha(R/'results/canonical-cache-replay-diagnosis.json')
  progress_path=D/'progress.json';progress=json.loads(progress_path.read_text()) if progress_path.exists() else dict(source_sha256=provenance,origins={},agreements={});assert progress['source_sha256']==provenance
  def mapping(name,width):
   path=D/name;shape=(1872,3060,width)
   if path.exists():
    value=np.load(path,mmap_mode='r+');assert value.shape==shape and value.dtype==np.float32;return value
   assert not progress['origins'];return np.lib.format.open_memmap(path,mode='w+',dtype=np.float32,shape=shape)
  features=mapping('features.npy',46);base=mapping('base-states.npy',4);rolling=np.load(F/'features.npy',mmap_mode='r');rolling_base=np.load(F/'base-states.npy',mmap_mode='r');largest_feature=0.;largest_state=np.zeros(4);largest_relative_mean=np.zeros(4);fit=np.array(plan['fit_indices']);fit_config=torch.tensor(a['configuration'][fit]);fit16_reference=groups(torch.tensor(np.abs(np.array(rolling_base[fit,:,-1])-a['truth'][fit,16:])).mean(1),fit_config).numpy()
  with torch.inference_mode():
   for origin,length in enumerate(lengths.tolist()):
    start,end=offsets[origin:origin+2];key=str(origin)
    if key in progress['origins']:
     hashes={n:hashlib.sha256(v[:,start:end].tobytes()).hexdigest() for n,v in [('features',features),('base',base)]};assert hashes==progress['origins'][key];agreement=progress['agreements'][key];largest_feature=max(largest_feature,agreement['max_feature']);largest_state=np.maximum(largest_state,agreement['max_state']);largest_relative_mean=np.maximum(largest_relative_mean,agreement['relative_mean']);continue
    prediction,x,b=predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+length+1],length,return_features=True);assert torch.isfinite(x).all() and torch.isfinite(b).all();x=x.numpy();b=b.numpy()
    agreement=dict(max_feature=0.,max_state=[0.]*4,relative_mean=[0.]*4)
    if origin<=74:
     reference=rolling[:,origin];reference_base=rolling_base[:,origin];difference=np.abs(b[:,:16]-reference_base);assert np.allclose(x[:,:16],reference,rtol=1e-4,atol=1e-4);assert np.allclose(b[:,:16],reference_base,rtol=1e-4,atol=np.array([.0001,.0002,.00002,.001]));relative=groups(torch.tensor(difference[fit]).mean(1),fit_config).numpy()/fit16_reference;assert (relative<=.001).all(),relative
     agreement=dict(max_feature=float(np.abs(x[:,:16]-reference).max()),max_state=difference.max((0,1)).tolist(),relative_mean=relative.tolist());largest_feature=max(largest_feature,agreement['max_feature']);largest_state=np.maximum(largest_state,agreement['max_state']);largest_relative_mean=np.maximum(largest_relative_mean,relative)
    if origin==0:assert np.allclose(x,a['features'][:,:length],rtol=1e-5,atol=3e-6) and np.allclose(b,a['base_states'][:,:length],rtol=1e-5,atol=3e-5)
    features[:,start:end]=x;base[:,start:end]=b;features.flush();base.flush();progress['agreements'][key]=agreement;progress['origins'][key]={n:hashlib.sha256(v[:,start:end].tobytes()).hexdigest() for n,v in [('features',features),('base',base)]};save(progress_path,progress)
    if origin%15==0:print('Completed origin',origin,'of89',flush=True)
  fit=np.array(plan['fit_indices']);config=torch.tensor(a['configuration'][fit]);normalization={}
  for h in [1,4,8,16,45]:
   origins=np.arange(91-h);endpoint=offsets[origins]+h-1;truth=a['truth'][fit[:,None],origins[None]+h];pred=np.array(base[fit[:,None],endpoint[None]]);error=torch.tensor(np.abs(pred-truth));normalization[str(h)]=dict(physical_MAE=groups(error.mean(1),config).tolist(),origins_per_history=len(origins),fit_histories=len(fit),fit_configurations=len(torch.unique(config)))
  np.save(D/'offsets.npy',offsets);np.save(D/'lengths.npy',lengths);np.save(D/'source-ids.npy',ids);save(D/'fit-normalization.json',normalization)
  assert all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
  metadata=dict(prepared=True,optimizer_updates=0,base_parameters_unchanged=True,histories=1872,fit_histories=1332,original_test_excluded=True,max_steps_per_origin=45,origins=90,stored_steps_per_history=3060,horizons_steps=[1,4,8,16,45],valid_stride_one_origins={str(h):91-h for h in [1,4,8,16,45]},role_plan_sha256=sha(C/'candidate-plan.json'),source_sha256=provenance,files={name:dict(sha256=sha(D/name),bytes=(D/name).stat().st_size) for name in ['features.npy','base-states.npy','offsets.npy','lengths.npy','source-ids.npy','fit-normalization.json']},prior_rolling_cache_agreement=dict(all1872_histories_all75_origins_checked=True,max_feature_absolute_error=largest_feature,max_state_absolute_error=largest_state.tolist(),maximum_fit_mean_difference_relative_to_fit16_MAE=largest_relative_mean.tolist(),comparison_policy='Feature rtol/atol1e-4; state rtol1e-4 with per-state absolute limits1e-4kg/2e-4kg/2e-5kg_s/1e-3heating_index. Every origin configuration-weighted fit mean state difference must be<=0.1percent of fit16baselineMAE. Based on independent prefix/batch-layout diagnosis; no model acceptance gate changed.'),normalization_fit_only=True,scope='Frozen original GRU observed-prefix forecasts only. Canonical windows1/4/8/16/45steps include every valid stride-one origin, with no artificial padding passed to the predictor. Fit/selection/development-confirmation roles unchanged; original208test histories absent. Preparing confirmation features is not confirmation scoring. Saved time grid/geometry/imposed20second ignition are known simulation inputs; no future target states enter forecast features. Same generic conical-crown FDS simplifications and derived-mass/sampled-release/signed-heating interpretations apply. No new fitting, accuracy claim or deployment.')
  save(R/'results/canonical-feature-cache-prepared.json',metadata);print(json.dumps({k:v for k,v in metadata.items() if k not in ['source_sha256','files']},indent=2))
if __name__=='__main__':main()
