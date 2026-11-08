"""Independent checks on two-case data, first-transition records and animations."""
from pathlib import Path
import json,hashlib,csv
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent

def main():
 results=[]
 for folder in sorted((R/'data/training-preview').iterdir()):
  if not folder.is_dir():continue
  d=np.load(folder/'training.npz');m=json.loads((folder/'metadata.json').read_text());s=json.loads((folder/'first-transition.json').read_text());a=json.loads((folder/'animation-verification.json').read_text());t=d['time_s'];x=d['state'];st=d['source_cone_time_s'];sy=d['source_cones']
  assert x.shape==(91,10) and np.isfinite(x).all() and t[0]==0 and t[-1]==180 and np.all(np.diff(t)>0)
  assert np.allclose(x[:,4:],np.column_stack([np.interp(t,st,sy[:,k]) for k in range(6)]),rtol=0,atol=1e-12)
  assert np.array_equal(d['cone_observed'],np.isin(t,st)) and np.array_equal(d['cone_interpolated'],~d['cone_observed'])
  assert np.all((d['cone_right_weight']>=0)&(d['cone_right_weight']<=1))
  assert np.isfinite(d['dt_next_s']).all() and np.array_equal(d['dt_next_s'][:-1],np.diff(t)) and not d['has_next_state'][-1]
  for label,j in [('initial_state',0),('next_state',1)]:
   assert np.array_equal(s[label]['values'],x[j]) and s[label]['time_s']==t[j]
  assert s['provenance']['no_historical_state_window'] and s['fixed_initial_conditions']==m['static_inputs']
  # Verify gas from the original CSV independently at every target timestamp.
  raw=next((R/'data/completed07').glob('*/'+folder.name+'/solve'))
  with (raw/(folder.name+'_devc.csv')).open() as f:rows=list(csv.reader(f))
  names=rows[1];v=np.array(rows[2:],float);cols=[j for j,n in enumerate(names) if n.endswith(' vapor')];assert len(cols)==7
  gas=np.interp(t,v[:,0],v[:,cols].sum(axis=1));assert np.allclose(gas,x[:,2],rtol=0,atol=1e-12)
  # Independent cumulative dry-fuel relation before interpolation.
  f=v[:,cols].sum(axis=1);dry=m['static_inputs']['initial_unreacted_fuel_kg']-np.r_[0,np.cumsum(np.diff(v[:,0])*(f[1:]+f[:-1])/2)]/.75
  assert np.allclose(np.interp(t,v[:,0],dry),x[:,1],rtol=0,atol=1e-9)
  with (raw/(folder.name+'_hrr.csv')).open() as file:hr=list(csv.reader(file))
  h=np.array(hr[2:],float);w=m['static_inputs']['initial_water_kg']-np.cumsum(h[:,hr[1].index('MLR_WATER VAPOR')]*np.r_[0,np.diff(h[:,0])]);assert np.allclose(np.interp(t,h[:,0],w),x[:,0],rtol=0,atol=1e-9)
  assert all(r.get('hot_recall',1)>=.95-1e-9 for r in m['cone_fit']) and m['initial_mass_matches_deck_design']
  assert hashlib.sha256((folder/'training.npz').read_bytes()).hexdigest()==m['training_npz_sha256']==a['training_npz_sha256']
  assert hashlib.sha256(x.tobytes()).hexdigest()==a['rendered_state_sha256'] and np.array_equal(a['rendered_time_s'],t)
  with Image.open(folder/'training-animation.gif') as im:assert im.n_frames==len(t)
  results.append({'case':folder.name,'passed':True,'rows':len(t),'source_cone_rows':len(st),'interpolated_cone_rows':int(d['cone_interpolated'].sum()),'frames':len(t),'initial_mass_design_match':True})
 assert len(results)==2
 report={'passed':True,'cases':results,'no_raw_deleted':True,'no_model_training':True};(R/'data/training-preview/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
