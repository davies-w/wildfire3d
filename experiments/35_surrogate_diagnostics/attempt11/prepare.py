"""Local archived-state extraction and auditable vector storyboards; no training."""
from pathlib import Path
import json,hashlib,tarfile,io,csv,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse,Polygon
from material_reader import frames
R=Path(__file__).resolve().parent;prior=R.parent/'attempt10';archive=R.parent.parent/'32_tree_expansion/data/cloud_archive'
cases=json.loads((prior/'cases.json').read_text());manifest=json.loads((R.parent/'attempt05/restore-manifest.json').read_text());out=R/'data/states';out.mkdir(exist_ok=True);figs=R/'data/storyboards';figs.mkdir(exist_ok=True)
xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in (48,32,32)],indexing='ij'),-1).reshape(-1,3)
def moments(w):
 w=w.reshape(-1).astype(float);s=w.sum()
 if s<=1e-12:return None
 c=(xyz*w[:,None]).sum(0)/s;d=xyz-c;cov=(d.T*w)@d/s
 return dict(centroid_m=c.tolist(),covariance_m2=cov.tolist(),rms_radius_m=float(np.sqrt(np.trace(cov))))
def readcsv(b):
 rows=list(csv.reader(io.StringIO(b.decode())));return [x.strip().strip('"') for x in rows[1]],np.array(rows[2:],float)
allrows=[];start=time.monotonic()
for c in cases:
 n=c['case'];dest=out/(n+'.json')
 if dest.exists():allrows.append(json.loads(dest.read_text()));continue
 item=next(i for i in manifest if i['target'].endswith('/'+n+'.tar.gz'));p=archive/item['archive_relative']
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==item['sha256']
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
 part.unlink();a=np.load(prior/'data/fields'/(n+'.npy'),mmap_mode='r');tt=np.load(prior/'data/fields'/(n+'-time.npy'));assert a.shape==(91,6,48,32,32)
 hk,ha=globalcsv[n+'_hrr.csv'];dk,da=globalcsv[n+'_devc.csv'];rows=[]
 for i,t in enumerate(tt):
  temp=np.array(a[i,0],float);q=np.maximum(a[i,1],0);hot=temp>50;w=np.where(hot,temp-20,0);mo=moments(w);hrrmo=moments(q);idx=int(np.argmin(abs(np.array(pt)-t)));gap=abs(pt[idx]-float(t));assert gap<.21
  centroid=np.array(mo['centroid_m']) if mo else None;root=np.array([8.,8.,2.+c['crown_height_m']/2]);delta=centroid-root if mo else None
  vel=(np.array(a[i,2:5])*w).reshape(3,-1).sum(1)/w.sum() if w.sum()>0 else None
  rad=np.array(a[i,5]);material=mats[idx];mass=sum(v['remaining_total_mass_kg'] for v in material)
  rows.append(dict(time_s=float(t),particle_time_s=pt[idx],alignment_error_s=gap,igniter_command_on=bool(t<20),gas_HRR_kW=float(q.sum()*.125),global_HRR_kW=float(np.interp(t,ha[:,0],ha[:,hk.index('HRR')])),solid_oxidation_HRR_kW=float(np.interp(t,ha[:,0],ha[:,hk.index('HRR_OX')])),fuel_vapor_release_kg_s=float(sum(np.interp(t,da[:,0],da[:,j]) for j,k in enumerate(dk) if k.startswith('v0 fuel'))),hot_volume_m3=float(hot.sum()*.125),peak_gas_temperature_C=float(temp.max()),temperature_excess_integral_K_m3=float(np.maximum(temp-20,0).sum()*.125),hot_plume=mo,hrr_region=hrrmo,plume_displacement_from_crown_m=delta.tolist() if mo else None,hot_weighted_velocity_m_s=vel.tolist() if vel is not None else None,mean_radiation_intensity=float(rad.mean()),max_radiation_intensity=float(rad.max()),remaining_total_material_mass_kg=mass,material_classes=material))
 result=dict(case=n,conditions=c,raw_sha256=item['sha256'],particle_quantities=units[:4],snapshots=rows,unavailable=['separate remaining dry fuel, water and char masses','gas thermal energy in joules (density/composition not captured here)','directional radiative flux at a receiving tree'],scope='Measured saved FDS fields and particles; derived moments are lossy summaries, not a trained state model. Initial particle frame may slightly follow zero; original timestamps retained.')
 dest.write_text(json.dumps(result,indent=2,allow_nan=False));allrows.append(result);print('PREPARED',n,round(time.monotonic()-start),flush=True)
(R/'data/states/index.json').write_text(json.dumps([dict(case=x['case'],conditions=x['conditions'],path=x['case']+'.json') for x in allrows],indent=2))
# Render every prepared development history at user-selected times.
for x in allrows:
 c=x['conditions'];fig,axs=plt.subplots(3,4,figsize=(20,16));target=[2,4,8,16,20,32,48,64,72,76,78,90];initial=x['snapshots'][0]['remaining_total_material_mass_kg']
 for ax,t in zip(axs.flat,target):
  r=min(x['snapshots'],key=lambda v:abs(v['time_s']-t));h=c['crown_height_m'];ax.add_patch(Polygon([[6.5,2],[9.5,2],[8,2+h]],facecolor='#bac6b6',edgecolor='#52664b',alpha=.7))
  mo=r['hot_plume']
  if mo:
   center=np.array(mo['centroid_m']);cov=np.array(mo['covariance_m2'])[np.ix_([0,2],[0,2])];ev,evec=np.linalg.eigh(cov);ang=np.degrees(np.arctan2(evec[1,1],evec[0,1]));ax.add_patch(Ellipse(center[[0,2]],4*np.sqrt(max(ev[1],0)),4*np.sqrt(max(ev[0],0)),angle=ang,facecolor='#ef983e',alpha=.35,edgecolor='#c76513'))
   ax.annotate('',xy=center[[0,2]],xytext=(8,2+h/2),arrowprops=dict(arrowstyle='->',color='#bc4c13',lw=2));ax.plot(*center[[0,2]],'o',color='#bc4c13',ms=4)
  else:ax.text(12,12,'No cells >50°C',ha='center',fontsize=9,color='#555555')
  ax.annotate('',xy=(2+c['wind_speed'],15),xytext=(2,15),arrowprops=dict(arrowstyle='->',color='#277da8',lw=2));ax.text(2,13.8,f"Ambient wind {c['wind_speed']:g} m/s",fontsize=8)
  mass=r['remaining_total_material_mass_kg'];mt=sum(v['remaining_total_mass_kg']*(v['mass_weighted']['PARTICLE TEMPERATURE'] or 0) for v in r['material_classes'])/mass if mass else 0
  ax.set(xlim=(0,24),ylim=(0,16),aspect='equal',title=f"{r['time_s']:.1f} s | igniter {'ON' if r['igniter_command_on'] else 'OFF'}",xlabel='x (m)',ylabel='height z (m)');ax.grid(alpha=.15)
  ax.text(0,-.29,f"Gas HRR {r['gas_HRR_kW']:,.2f} kW | HOT {r['hot_volume_m3']:.2f} m³\nMaterial {mass:.2f} kg ({100*mass/initial:.1f}% initial) | {mt:.1f}°C",transform=ax.transAxes,fontsize=9)
 fig.suptitle(f"{x['case']} · crown {c['crown_height_m']:g} m · moisture {c['moisture']:.0%} dry basis · loading {c['loading_multiplier']:g} · ignition angle {c['angle_deg']:g}°\nSide-view storyboard from FDS: orange arrow crown centre → hot-gas centroid; ellipse = 2σ temperature-weighted extent (not flame boundary)",fontsize=14)
 fig.text(.5,.015,'Generic 3 m-wide crown above 2 m; 0.5 m grid; artificial 1500°C / 20 s igniter; no trunks/buildings/embers.\nMass includes water/reaction products. Ellipse and arrow are derived summaries; HOT means gas >50°C, not combustion. View collapses y; full 3-D moments retained.',ha='center',fontsize=10)
 fig.subplots_adjust(top=.84,bottom=.13,hspace=.72,wspace=.25);fig.savefig(figs/(x['case']+'.png'),dpi=130);plt.close(fig)
proof=dict(cases=len(allrows),snapshots=sum(len(x['snapshots']) for x in allrows),storyboards=len(allrows),storyboard_times_s=[2,4,8,16,20,32,48,64,72,76,78,90],max_particle_alignment_s=max(r['alignment_error_s'] for x in allrows for r in x['snapshots']),training=False,new_simulations=False)
(R/'results/prepared.json').write_text(json.dumps(proof,indent=2));print(proof)
