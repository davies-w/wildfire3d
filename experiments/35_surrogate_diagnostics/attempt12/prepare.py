"""Prepare all 520 archived histories locally, one case at a time; no fitting."""
from pathlib import Path
import json,hashlib,tarfile,io,csv,time,shutil,fcntl
import numpy as np
from material_reader import frames
import fields
R=Path(__file__).resolve().parent;E=R.parent.parent
items=json.loads((R/'inventory.json').read_text());out=R/'data/states';out.mkdir(exist_ok=True);(R/'data/cloud').mkdir(exist_ok=True)
lock=(R/'data/prepare.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in (48,32,32)],indexing='ij'),-1).reshape(-1,3)
def moments(w):
 w=w.reshape(-1).astype(float);s=w.sum()
 if s<=1e-12:return None
 c=(xyz*w[:,None]).sum(0)/s;d=xyz-c;cov=(d.T*w)@d/s
 return dict(centroid_m=c.tolist(),covariance_m2=cov.tolist(),rms_radius_m=float(np.sqrt(np.trace(cov))))
def readcsv(b):
 rows=list(csv.reader(io.StringIO(b.decode())));return [x.strip().strip('"') for x in rows[1]],np.array(rows[2:],float)
index=[];start=time.monotonic()
for item in items:
 c=item['conditions'];n=c['case'];dest=out/(n+'.json')
 if dest.exists():
  old=json.loads(dest.read_text());assert old['case']==n
  index.append(dict(case=n,snapshots=len(old['snapshots']),source=item['source'],archive_sha256=old['raw_sha256']));continue
 p=E/item['archive']
 with p.open('rb') as f:actual_hash=hashlib.file_digest(f,'sha256').hexdigest()
 if item['expected_sha256']:assert actual_hash==item['expected_sha256']
 item=dict(item,sha256=actual_hash)
 folder=R/'data/cloud'/n;folder.mkdir(parents=True,exist_ok=True)
 with tarfile.open(p) as tar:
  for m in tar:
   if m.isfile() and m.name.endswith(('.sf','_devc.csv')):
    with tar.extractfile(m) as src,(folder/Path(m.name).name).open('wb') as dst:shutil.copyfileobj(src,dst)
 fields.extract(c)
 part=R/'data/particle.tmp';globalcsv={};units=[];deck=''
 with tarfile.open(p) as tar:
  for m in tar:
   if m.name.endswith('_1.prt5'):part.write_bytes(tar.extractfile(m).read())
   elif m.name.endswith(('_hrr.csv','_devc.csv')):globalcsv[Path(m.name).name]=readcsv(tar.extractfile(m).read())
   elif m.name.endswith('.fds'):deck=tar.extractfile(m).read().decode()
 # Preserve units directly from binary headers.
 from fortran_records import FortranFile
 f=FortranFile(part);f.read_ints();f.read_ints()
 for k in range(int(f.read_ints()[0])):
  names=[]
  for j in range(int(f.read_ints()[0])):names.append(dict(name=f.read_record('u1').tobytes().decode().strip(),unit=f.read_record('u1').tobytes().decode().strip()))
  units.append(names)
 del f
 mats=[];pt=[]
 for t,ps,labels in frames(part):
  if not sum(len(x) for x,q in ps[:4]):continue
  classes=[]
  for k,(pos,q) in enumerate(ps[:4]):
   assert labels[k][:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR']
   mw=q[:,1]*q[:,2];s=float(mw.sum());vals={lab:float(np.sum(mw*q[:,j])/s) if s else None for j,lab in enumerate(labels[k]) if j not in (1,2)}
   classes.append(dict(class_name=['foliage','small roundwood','medium roundwood','large roundwood'][k],remaining_total_mass_kg=s,mass_weighted=vals,particle_count=len(pos)))
  mats.append(classes);pt.append(t)
 part.unlink();a=np.load(R/'data/fields'/(n+'.npy'),mmap_mode='r');tt=np.load(R/'data/fields'/(n+'-time.npy'));assert a.shape[1:]==(6,48,32,32) and len(tt)==len(a) and tt[-1]>=179.9
 hk,ha=globalcsv[n+'_hrr.csv'];dk,da=globalcsv[n+'_devc.csv'];rows=[]
 for i,t in enumerate(tt):
  temp=np.array(a[i,0],float);q=np.maximum(a[i,1],0);hot=temp>50;w=np.where(hot,temp-20,0);mo=moments(w);hrrmo=moments(q);idx=int(np.argmin(abs(np.array(pt)-t)));gap=abs(pt[idx]-float(t));assert gap<.21
  centroid=np.array(mo['centroid_m']) if mo else None;root=np.array([8.,8.,2.+c.get('crown_height_m',8.)/2]);delta=centroid-root if mo else None
  vel=(np.array(a[i,2:5])*w).reshape(3,-1).sum(1)/w.sum() if w.sum()>0 else None
  rad=np.array(a[i,5]);material=mats[idx];mass=sum(v['remaining_total_mass_kg'] for v in material)
  rows.append(dict(time_s=float(t),particle_time_s=pt[idx],alignment_error_s=gap,igniter_command_on=bool(t<20),gas_HRR_kW=float(q.sum()*.125),global_HRR_kW=float(np.interp(t,ha[:,0],ha[:,hk.index('HRR')])),solid_oxidation_HRR_kW=float(np.interp(t,ha[:,0],ha[:,hk.index('HRR_OX')])),fuel_vapor_release_kg_s=float(sum(np.interp(t,da[:,0],da[:,j]) for j,k in enumerate(dk) if k.startswith('v0 fuel'))),hot_volume_m3=float(hot.sum()*.125),peak_gas_temperature_C=float(temp.max()),temperature_excess_integral_K_m3=float(np.maximum(temp-20,0).sum()*.125),hot_plume=mo,hrr_region=hrrmo,plume_displacement_from_crown_m=delta.tolist() if mo else None,hot_weighted_velocity_m_s=vel.tolist() if vel is not None else None,mean_radiation_intensity=float(rad.mean()),max_radiation_intensity=float(rad.max()),remaining_total_material_mass_kg=mass,material_classes=material))
 result=dict(case=n,conditions=c,raw_sha256=item['sha256'],particle_quantities=units[:4],snapshots=rows,unavailable=['separate remaining dry fuel, water and char masses','gas thermal energy in joules (density/composition not captured here)','directional radiative flux at a receiving tree'],scope='Measured saved FDS fields and particles; derived moments are lossy summaries, not a trained state model. Initial particle frame may slightly follow zero; original timestamps retained.')
 dest.write_text(json.dumps(result,indent=2,allow_nan=False));index.append(dict(case=n,snapshots=len(rows),source=item['source'],archive_sha256=actual_hash));del a
 shutil.rmtree(folder)
 for q in (R/'data/fields').glob(n+'*'):q.unlink()
 print('PREPARED',n,len(rows),round(time.monotonic()-start),flush=True)

(out/'index.json').write_text(json.dumps(index,indent=2))
proof=dict(complete=True,histories=len(index),snapshots=sum(x['snapshots'] for x in index),transitions=sum(x['snapshots']-1 for x in index),new_histories=sum(x['source']=='exp32_new' for x in index),legacy_histories=sum(x['source']=='legacy' for x in index),training=False)
(R/'results/prepared.json').write_text(json.dumps(proof,indent=2));print(proof,flush=True)
