"""Extract spatial surface-heating moments from archived particle records; no training."""
from pathlib import Path
import tarfile,json,hashlib,fcntl
import numpy as np
from material_reader import frames
R=Path(__file__).resolve().parent;E=R.parents[1];P=R.parent/'attempt12';items=json.loads((P/'inventory.json').read_text());base=np.load(R.parent/'attempt19/data/thermal_candidates.npz')
(R/'data/cases').mkdir(exist_ok=True);lock=(R/'data/prepare.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
allv=[];proof=[]
for i,it in enumerate(items):
 name=it['conditions']['case'];dest=R/'data/cases'/f'{name}.npz';source=E/it['archive'];expected=json.loads((P/'data/states'/f'{name}.json').read_text())['raw_sha256']
 if not dest.exists():
  with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  assert digest==expected
  tmp=R/'data/particle.tmp'
  with tarfile.open(source) as tar:
   found=False
   for m in tar:
    if m.name.endswith('_1.prt5'):
     tmp.write_bytes(tar.extractfile(m).read());found=True;break
   assert found
  ts=[];vals=[];reference=None;initialmass=None
  for t,ps,labels in frames(tmp):
   if not sum(len(p) for p,q in ps[:4]):continue
   xyz=np.concatenate([p for p,q in ps[:4]],0).astype(float);qs=np.concatenate([q for p,q in ps[:4]],0).astype(float)
   assert all(x[:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR'] for x in labels[:4])
   mass=qs[:,1]*qs[:,2];assert (mass>=0).all()
   if reference is None:initialmass=float(mass.sum());reference=(xyz*mass[:,None]).sum(0)/initialmass
   excess=qs[:,0]-20;w=mass*np.maximum(excess,0);dipole=((xyz-reference)*w[:,None]).sum(0)/initialmass
   positive=float(w.sum()/initialmass);signed=float((mass*excess).sum()/initialmass)
   vals.append([signed,positive,*dipole]);ts.append(t)
  tmp.unlink();ts=np.array(ts);vals=np.array(vals);want=base['time'][i];ix=np.abs(ts[:,None]-want).argmin(0);assert max(abs(ts[ix]-want))<.21
  v=vals[ix];assert np.isfinite(v).all();delta=float(np.max(abs(v[:,0]-base['thermal'][i])));assert delta<.002,(name,delta)
  np.savez_compressed(dest,values=v,time=want,reference=reference,initial_mass=initialmass,sha256=digest,scalar_agreement=delta)
 with np.load(dest) as z:
  v=z['values'];assert str(z['sha256'])==expected;allv.append(v);proof.append(dict(case=name,raw_sha256=expected,scalar_max_difference_K=float(z['scalar_agreement']),initial_material_centroid_m=z['reference'].tolist()))
 if i%25==0:print('EXTRACTED',i+1,flush=True)
v=np.array(allv);np.savez_compressed(R/'data/spatial_candidates.npz',values=v,time=base['time']);present=v[:,:,1]>.01;displacement=np.linalg.norm(v[:,:,2:]/np.maximum(v[:,:,1,None],1e-12),axis=-1)
summary=dict(histories=520,shape=list(v.shape),columns=['signed_surface_index_K','positive_surface_index_K','heating_dipole_x_Km','heating_dipole_y_Km','heating_dipole_z_Km'],anchor='Measured initial vegetation mass centroid for each history; not ignition point or arbitrary crown anchor.',meaning='Mass-weighted positive particle-surface temperature excess first spatial moment / initial mass; vector indicates location asymmetry, NOT heat flow, energy, plume velocity or length.',presence_for_summary='positive surface index >0.01K; no threshold applied to moment labels',present_fraction=float(present.mean()),heating_centroid_displacement_quantiles_m=np.quantile(displacement[present],[.25,.5,.75,.95,1]).tolist(),maximum_scalar_reconstruction_difference_K=max(p['scalar_max_difference_K'] for p in proof),records=proof,training=False)
(R/'results/audit.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)
