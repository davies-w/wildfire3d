"""Validate existing four-state observations, with no cone fitting or model training."""
from pathlib import Path
import json,gzip,hashlib
import numpy as np
R=Path(__file__).resolve().parent;ROOT=R.parents[1];SOURCE=R.parent/'51_three_tree_campaign'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'data';out.mkdir(exist_ok=True);records=[];states=[];times=[];fixed=[]
 cases={c['case']+'_baseline':c for c in map(json.loads,gzip.open(SOURCE/'data/cases.jsonl.gz','rt'))}
 for d in sorted((SOURCE/'private07/continuous-training').glob('tree51_*')):
  complete=d/'complete.json';defer=d/'deferred.json'
  if complete.exists():
   proof=json.loads(complete.read_text());assert proof['passed'] and proof['training_retained'];folder=SOURCE/'data/training-both-formats'/d.name/'cone'
  elif defer.exists():folder=d/'generated/base'/d.name
  else:continue
  meta=json.loads((folder/'metadata.json').read_text());f=folder/'training.npz';assert sha(f)==meta['training_npz_sha256'];a=np.load(f);state=a['state'][:,:4].copy();t=a['time_s'].copy()
  base=d/'generated/base'/d.name
  if not (base/'metadata.json').exists():
   candidates=[]
   for mp in (SOURCE/'data').glob('**/'+d.name+'/metadata.json'):
    candidate=json.loads(mp.read_text())
    if candidate.get('initial_mass_matches_deck_design') and candidate.get('training_npz_sha256')==meta.get('original_four_state_npz_sha256'):candidates.append(mp.parent)
   assert candidates, d.name
   base=sorted(candidates)[0]
  bm=json.loads((base/'metadata.json').read_text());bf=base/'training.npz';assert bm['initial_mass_matches_deck_design'] and sha(bf)==bm['training_npz_sha256'];ba=np.load(bf);assert np.array_equal(state,ba['state'][:,:4]) and np.array_equal(t,ba['time_s'])
  assert state.shape==(91,4) and np.isfinite(state).all() and (np.ptp(state,axis=0)>0).all();assert t[0]==0 and t[-1]==180 and (np.diff(t)>0).all();assert state[:,:3].min()>-1e-6
  if complete.exists():
   b=np.load(folder.parent/'free_cone/training.npz');assert np.array_equal(state,b['state'][:,:4]) and np.array_equal(t,b['time_s'])
  else:
   # These are observations extracted before the separate anchored fitting failure.
   raw=json.loads((d/'raw-verified.json').read_text());assert raw['passed']
  s=meta['static_inputs'];assert s['ignition_mode'] in ('base','crown');v=[*s['tree_family_one_hot_pine_oak_eucalyptus'],s['total_height_m'],s['crown_base_height_m'],s['crown_width_m'],*s['ignition_contact_relative_xyz_m'],int(s['ignition_mode']=='crown'),s['wind_speed_m_s'],s['moisture_dry_basis_fraction'],s['loading_multiplier'],s['initial_water_kg'],s['initial_unreacted_fuel_kg']];assert len(v)==15
  assert np.allclose(state[0,:2],v[-2:],rtol=1e-12,atol=1e-8)
  c=cases[d.name];records.append({'case':d.name,'source_case':meta.get('source_case',d.name),'family':s['tree_family'],'environment':[c['wind_m_s'],c['moisture_fraction']],'physical_configuration':[c['geometry_id'],c['ignition_index'],c['wind_m_s'],c['moisture_fraction'],c['loading_multiplier']],'source_npz':str(f.relative_to(ROOT)),'source_npz_sha256':sha(f),'cone_fit_previously_deferred':not complete.exists(),'original_split':c['split']})
  states.append(state);times.append(t);fixed.append(v)
 assert len(records)==1899 and sum(x['cone_fit_previously_deferred'] for x in records)==19
 state=np.array(states);time=np.array(times);fixed=np.array(fixed);dt=np.diff(time)
 # Same trailing five-interval gate definitions and thresholds as the earlier model.
 j=np.arange(1,91);k=np.maximum(j-5,0);elapsed=time[:,j]-time[:,k];q=np.maximum(state[:,:,2],0);cum=np.c_[np.zeros(len(state)),np.cumsum((q[:,1:]+q[:,:-1])*.5*dt,axis=1)]
 water=np.maximum(state[:,k,0]-state[:,j,0],0)/state[:,0,0,None]/elapsed;fuel=np.maximum(state[:,k,1]-state[:,j,1],0)/state[:,0,1,None]/elapsed;gas=(cum[:,j]-cum[:,k])/.75/state[:,0,1,None]/elapsed;rates=np.stack([water,fuel,gas],-1)
 # Actual prescribed ignition ramp integrated over each interval; no future state input.
 def primitive(t):return np.where(t<.1,5*t*t,np.where(t<=20,t-.05,np.where(t<20.1,19.95+(t-20)-5*(t-20)**2,20.0)))
 on=(primitive(time[:,1:])-primitive(time[:,:-1]))/dt;assert ((on>=-1e-8)&(on<=1+1e-8)).all()
 configs={};configuration=[]
 for c in records:
  key=tuple(c['physical_configuration']);configs.setdefault(key,len(configs));configuration.append(configs[key])
 np.savez_compressed(out/'observations.npz',state=state,time=time,geometry=fixed,configuration=np.array(configuration),ignition_on_fraction=on,gate_rates=rates,gate_targets=(rates>=1e-4).astype('float32'),gate_supervised=((rates<1e-5)|(rates>=1e-4)))
 schema={'cases':records,'state_names':['remaining_water','remaining_unreacted_fuel','fuel_gas_release_rate','surface_heating_index'],'state_units':['kg','kg','kg/s','K'],'static_names':['pine','oak','eucalyptus','total_height_m','crown_base_height_m','crown_width_m','ignition_relative_x_m','ignition_relative_y_m','ignition_height_m','crown_ignition','wind_m_s','moisture_dry_basis_fraction','loading_multiplier','initial_water_kg','initial_unreacted_fuel_kg'],'physical_encoding_scales':[1,1,.01,100],'history_samples':8,'external_features':17,'model_inputs':49,'observations_sha256':sha(out/'observations.npz'),'limitations':['Species-inspired geometries with generic fuel, not calibrated species.','Heating is a temperature-based index in K, not energy.','Original .5m mesh, imposed contact ignition; no embers/bark/grass/resolved solid trunk.','No cone inputs, labels, objectives, or cone-based exclusions.','Historical previews have been inspected; this is not a pristine unseen dataset.'],'normalization':'Train configurations only; preserve asinh four-state encoding; continuous fixed features train-normalized, categorical indicators unchanged; dt/2.'}
 (out/'source-schema.json').write_text(json.dumps(schema,indent=2)+'\n');print('PASS1899 four-state histories,including19 cone-deferred cases;no model training',flush=True)
if __name__=='__main__':main()
