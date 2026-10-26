"""Merge all verified histories and frozen grouped folds. No normalization or fitting."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'35_surrogate_diagnostics'

def labels(s,t):
 q=np.maximum(s[:,:,2],0);dt=np.diff(t);gas=(q[:,1:]+q[:,:-1])*.5*dt
 cum=np.c_[np.zeros(len(s)),np.cumsum(gas,axis=1)];j=np.arange(1,91);k=np.maximum(j-5,0);elapsed=t[:,j]-t[:,k]
 fuel=(cum[:,j]-cum[:,k])/.75/s[:,0,1,None]/elapsed
 water=np.maximum(s[:,k,0]-s[:,j,0],0)/s[:,0,0,None]/elapsed
 releasing=fuel>=1e-4;drying=(water>=1e-4)&~releasing;quiet=(fuel<1e-5)&(water<1e-5)
 return np.select([releasing,drying,quiet],[1,2,0],default=3).astype('uint8')

def main():
 manifest=json.loads((R/'data/grouped-folds.json').read_text());cases=json.loads((R/'cases.json').read_text())
 audit=json.loads((R/'results/four-state-extraction.json').read_text());assert audit['histories']==1560 and not audit['awaiting_exact_timestamps'],'Full verified dataset required'
 assert {x['case'] for x in audit['cases']}=={c['case'] for c in cases}
 old=np.load(OLD/'attempt20/data/sequences.npz');meta=json.loads((OLD/'attempt20/schema.json').read_text());newstate=[];newtime=[];newgeometry=[]
 assert [c['case'] for c in manifest['cases'][:520]]==[c['case'] for c in meta['cases']]
 for c in cases:
  name=c['case'];proof=json.loads((R/'data/verified-material'/name/'verified.json').read_text());assert proof['checkpoint_hashes_verified']
  row=next(x for x in audit['cases'] if x['case']==name);assert proof['raw_sha256']==row['raw_sha256']
  a=np.load(R/'data/four-state'/(name+'.npz'));s=a['state'];t=a['time'];assert s.shape==(91,4) and t.shape==(91,) and np.isfinite(s).all()
  newstate.append(s);newtime.append(t);newgeometry.append([c['crown_height_m'],c['loading_multiplier'],c['wind_speed'],np.cos(np.deg2rad(c['angle_deg'])),np.sin(np.deg2rad(c['angle_deg'])),s[0,0],s[0,1]])
 s=np.concatenate([old['state'],np.array(newstate)],axis=0);t=np.concatenate([old['time'],np.array(newtime)],axis=0);g=np.concatenate([old['geometry'],np.array(newgeometry,dtype='float32')],axis=0)
 assert s.shape==(2080,91,4) and g.shape==(2080,7) and np.array_equal(s[:520],old['state']) and np.array_equal(t[:520],old['time'])
 lab=labels(s,t);prior=np.load(OLD/'attempt22/data/activity_audit/labels.npz')['labels'];assert np.array_equal(lab[:520],prior),'Frozen activity definition changed'
 keys=[tuple(c['physical_key']) for c in manifest['cases']];unique=sorted(set(keys));lookup={k:i for i,k in enumerate(unique)};config=np.array([lookup[k] for k in keys],dtype='int64');fold=np.array([c['fold'] for c in manifest['cases']],dtype='int64')
 assert len(unique)==2040 and all(len(set(fold[config==i]))==1 for i in range(2040))
 dest=R/'data/learning';dest.mkdir(exist_ok=True);np.savez_compressed(dest/'sequences.npz',state=s,time=t,geometry=g,configuration=config,fold=fold,activity_labels=lab)
 meta.update(cases=manifest['cases'],rotations=manifest['rotations'],histories=2080,configurations=2040,transitions=187200,comparison='Unchanged plain four-state GRU on denser in-range simulation data',scope='Generic cones and derived material states; no physical validation. Previously examined old data, not historically pristine. Grouped reshuffle preserves replicas. No gates or clamps.',scorecard_sha256=hashlib.sha256((OLD/'scorecard-v1.json').read_bytes()).hexdigest())
 (R/'learning-schema.json').write_text(json.dumps(meta,indent=2)+'\n')
 report={'histories':2080,'new_histories':1560,'configurations':2040,'old_states_times_bitwise_preserved':True,'old_activity_labels_exact':True,'replicas_grouped':True,'training':False,'normalization_fitted':False,'sequences_sha256':hashlib.sha256((dest/'sequences.npz').read_bytes()).hexdigest()}
 (R/'results/learning-data.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
