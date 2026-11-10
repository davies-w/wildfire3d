"""Two backed-up cases only: raw-derived ten-state data and faithful previews.

No solver/model training, no raw deletion. Uses an independently HF-restored
archive to verify every local extraction input. Cone interpolation is synthetic.
"""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,re,struct,sys,tarfile
import numpy as np
R=Path(__file__).resolve().parent; ROOT=R.parents[1]
sys.path.insert(0,str(R.parent/'36_tree_density'))
from material_reader import frames
from interpolate_cone_labels import interpolate_cones
NAMES=['remaining_water','remaining_unreacted_fuel','fuel_gas_release_rate','surface_heating_index','cone_presence','cone_pivot_height','cone_tilt_from_vertical','cone_axial_length','cone_end_radius','cone_peak_temperature']
UNITS=['kg','kg','kg/s','K','fraction','m','degrees','m','m','degC']
FAMILY={1:'pine-inspired',2:'oak-inspired',3:'eucalyptus-inspired'}

SOLVE_OVERRIDES={}
def solve_folder(case):
 if case in SOLVE_OVERRIDES:return Path(SOLVE_OVERRIDES[case])
 return next((R/'data/completed07').glob('*/'+case+'/solve'))

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(f):
 b=f.read(4)
 if not b:return None
 n=struct.unpack('<I',b)[0];a=f.read(n);tail=f.read(4)
 assert len(a)==n and struct.unpack('<I',tail)[0]==n
 return a

def temperatures(path,domain,dx):
 with path.open('rb') as f:
  assert record(f).decode().strip()=='TEMPERATURE';record(f);assert record(f).decode().strip()=='C'
  bounds=np.frombuffer(record(f),'<i4');n=np.rint(np.array(domain)/dx).astype(int)
  assert np.array_equal(bounds,np.array([[0,k] for k in n]).reshape(-1))
  # SLCC cell-centred output: interior cell i is at (i-.5)*dx, i=1..I.
  shape=tuple(n+1)
  while (b:=record(f)) is not None:
   t=float(np.frombuffer(b,'<f4')[0]);a=np.frombuffer(record(f),'<f4').reshape(shape,order='F')[1:,1:,1:]
   assert np.isfinite(a).all();yield t,a.astype(float)

def axis(tilt):
 a=np.deg2rad(tilt);return np.array([np.sin(a),0,np.cos(a)])
def candidate(points,center,pivot,tilt):
 d=points-np.r_[center,pivot];s=d@axis(tilt);positive=s>1e-8;k=int(np.ceil(.95*len(points)))
 if positive.sum()<k:return None
 s=s[positive];d=d[positive];length=float(s.max());slopes=np.sqrt(np.maximum((d*d).sum(1)-s*s,0))/s
 radius=float(np.partition(slopes,k-1)[k-1]*length)
 return (np.pi*radius**2*length/3,float(pivot),float(tilt),length,radius)
def cone_row(xyz,temp,geometry,center,shape):
 hot=temp>50
 if not hot.any():return np.zeros(6),{'active':False,'hot_cells':0,'domain_peak_C':float(temp.max())}
 points=xyz[hot];sample=points if len(points)<=1024 else points[np.sort(np.random.default_rng(3516).choice(len(points),1024,replace=False))]
 candidates=[candidate(sample,center,h,a) for h in np.unique(np.r_[0,np.linspace(geometry['crown_base_m'],geometry['total_height_m'],7)]) for a in range(0,91,10)]
 candidates=sorted(c for c in candidates if c is not None)
 final=[candidate(points,center,c[1],c[2]) for c in candidates[:8]];final=[c for c in final if c is not None]
 c=min(final or [candidate(points,center,0,0)]);volume,h,tilt,length,radius=c
 d=xyz-np.r_[center,h];s=d@axis(tilt);radial=np.maximum((d*d).sum(1)-s*s,0)
 mask=(s>=0)&(s<=length+1e-9)&(radial<=(radius*s/length)**2+1e-9)
 tp=int((mask&hot).sum());recall=tp/int(hot.sum());assert recall>=.95-1e-9
 grid=hot.reshape(shape);boundary=np.zeros(shape,bool)
 for k in range(3):
  sl=[slice(None)]*3;sl[k]=0;boundary[tuple(sl)]=True;sl[k]=-1;boundary[tuple(sl)]=True
 return np.array([1,h,tilt,length,radius,float(temp[mask].max())]),dict(active=True,hot_cells=int(hot.sum()),hot_recall=recall,hot_precision=tp/int(mask.sum()),domain_peak_C=float(temp.max()),hot_boundary_cells=int(grid[boundary].sum()),cone_volume_m3=volume)

def table(p):
 with p.open() as f:r=list(csv.reader(f))
 return r[1],np.array(r[2:],float)
SOURCE_CASE_OVERRIDES={}
def source_case(case):return SOURCE_CASE_OVERRIDES.get(case,case)

def extract(source,out):
 case=source['case'];c=next(json.loads(s) for s in gzip.open(R/'data/cases.jsonl.gz','rt') if json.loads(s)['case']==case.removesuffix('_baseline'))
 g=next(g for g in json.loads((R/'data/geometries.json').read_text()) if g['id']==c['geometry_id'])
 raw_case=source_case(case);folder=solve_folder(case);proof=json.loads((folder.parent/'proof.json').read_text());assert proof['passed'] and proof['physical_time_s']==180
 needed=[folder/'input.fds',folder/(raw_case+'_1.prt5'),folder/(raw_case+'_hrr.csv'),folder/(raw_case+'_devc.csv'),folder/(raw_case+'_1_1.sf'),folder/(raw_case+'.smv')]
 hashes={}
 if source.get('restoration_receipt'):
  receipt=json.loads(Path(source['restoration_receipt']).read_text());assert receipt['passed'] and source['HF_restored']
  for p in needed:
   h=sha(p);assert next(x['sha256'] for x in proof['files'] if x['path']=='solve/'+p.name)==h
   assert receipt['raw_inputs_sha256'][source['original_solve']+'/'+p.name]==h;hashes[p.name]=h
 else:
  archive=Path(source['archive']);archive=archive if archive.is_absolute() else ROOT/archive
  if not archive.exists():archive=ROOT/'.artifact-staging/two-case-preview-restored'/Path(source['archive'])
  assert sha(archive)==source['sha256'] and source['HF_restored']
  with tarfile.open(archive) as tf:
   for p in needed:
    h=sha(p);assert next(x['sha256'] for x in proof['files'] if x['path']=='solve/'+p.name)==h
    member=tf.extractfile('evidence/solve/'+p.name);assert hashlib.file_digest(member,'sha256').hexdigest()==h;hashes[p.name]=h
 text=(folder/'input.fds').read_text();smv=(folder/(raw_case+'.smv')).read_text();assert 'SLCC' in smv
 parts=re.findall(r'&PART\b.*?/',text,re.S);ids=[re.search(r"\bID\s*=\s*'([^']+)'",p)[1] for p in parts]
 selected=[i for i,n in enumerate(ids) if n!='contact ignitor'];expected_classes=(source['expected_wet_mass_kg'] if 'expected_wet_mass_kg' in source else next(x['expected_wet_mass_kg'] for x in json.loads((R/'data/decks/cases.json').read_text()) if x['pilot_case']==case));assert set(ids[i] for i in selected)==set(expected_classes) and ids.count('contact ignitor')==1
 surfaces=re.findall(r'&SURF\b.*?/',text,re.S)
 for i in selected:
  surf=next(b for b in surfaces if re.search(r"\bID\s*=\s*'"+re.escape(ids[i])+"'",b))
  assert 'GENERIC VEGETATION' in surf and abs(float(re.search(r'MOISTURE_CONTENT\s*=\s*([\d.]+)',surf)[1])-c['moisture_fraction'])<1e-9
 pt=[];masses=[];weighted=[];initial_xyz=None;class_masses=None
 for t,ps,labels in frames(folder/(raw_case+'_1.prt5')):
  assert len(ps)==len(ids);mm=[];heat=0
  for i in selected:
   pos,q=ps[i];assert labels[i][:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR'];q=q.astype(float);mass=q[:,1]*q[:,2];mm.append(float(mass.sum()));heat+=float(np.sum(mass*(q[:,0]-20)))
  if initial_xyz is None:initial_xyz=np.concatenate([ps[i][0] for i in selected]);class_masses=dict(zip([ids[i] for i in selected],mm))
  pt.append(t);masses.append(sum(mm));weighted.append(heat)
 target=np.array(pt);assert len(target)==91 and target[0]==0 and target[-1]==180 and np.all(np.diff(target)>0)
 expected=(source['expected_wet_mass_kg'] if 'expected_wet_mass_kg' in source else next(x['expected_wet_mass_kg'] for x in json.loads((R/'data/decks/cases.json').read_text()) if x['pilot_case']==case))
 assert all(abs(class_masses[k]/v-1)<1e-5 for k,v in expected.items())
 wet0=masses[0];dry0=wet0/(1+c['moisture_fraction']);water0=wet0-dry0
 assert wet0>0
 hk,h=table(folder/(raw_case+'_hrr.csv'));dk,a=table(folder/(raw_case+'_devc.csv'));ht=h[:,0];at=a[:,0]
 assert np.all(np.diff(ht)>0) and np.all(np.diff(at)>0) and ht[0]==at[0]==0 and ht[-1]>=180 and at[-1]>=180
 cols=[dk.index(ids[i]+' vapor') for i in selected];fuel=a[:,cols].sum(1)
 water=water0-np.cumsum(h[:,hk.index('MLR_WATER VAPOR')]*np.diff(ht,prepend=0))
 dry=dry0-np.r_[0,np.cumsum((fuel[:-1]+fuel[1:])*.5*np.diff(at))]/.75
 four=np.stack([np.interp(target,ht,water),np.interp(target,at,dry),np.interp(target,at,fuel),np.array(weighted)/wet0],axis=1)
 assert np.isfinite(four).all() and four[:,:3].min()>-1e-6
 domain=c['domain'];dx=c['dx'];shape=tuple(np.rint(np.array(domain)/dx).astype(int));center=np.array(domain[:2])/2
 xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*dx for n in shape],indexing='ij'),-1).reshape(-1,3)
 times=[];cones=[];fit=[]
 for t,temp in temperatures(folder/(raw_case+'_1_1.sf'),domain,dx):
  row,audit=cone_row(xyz,temp.reshape(-1),g,center,shape);times.append(t);cones.append(row);fit.append({'time_s':t,**audit})
 assert len(times)>=6 and times[0]==0 and times[-1]==180
 interp=interpolate_cones(times,cones,target);assert np.array_equal(interpolate_cones(times,cones,np.array(times))['cones'],np.array(cones))
 state=np.column_stack([four,interp['cones']]);ig=g['ignitions'][c['ignition_index']]
 static={'tree_family':FAMILY[c['type_id']],'tree_family_one_hot_pine_oak_eucalyptus':[int(c['type_id']==i) for i in [1,2,3]],'total_height_m':g['total_height_m'],'crown_base_height_m':g['crown_base_m'],'crown_width_m':2*g['crown_radius_m'],'ignition_contact_relative_xyz_m':ig['contact_xyz_m'],'ignition_mode':ig['mode'],'wind_speed_m_s':c['wind_m_s'],'moisture_dry_basis_fraction':c['moisture_fraction'],'loading_multiplier':c['loading_multiplier'],'initial_water_kg':water0,'initial_unreacted_fuel_kg':dry0}
 # Match the actual ramp: .1 s on-ramp, steady to20, .1 s off-ramp.
 ignition=np.interp(target,[0,.1,20,20.1,180],[0,1,1,0,0])
 dest=out/case;dest.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(dest/'training.npz',time_s=target,state=state,state_names=np.array(NAMES),state_units=np.array(UNITS),source_cone_time_s=interp['source_time_s'],source_cones=interp['source_cones'],cone_observed=interp['observed'],cone_interpolated=interp['interpolated'],cone_left_source_index=interp['left_source_index'],cone_right_source_index=interp['right_source_index'],cone_right_weight=interp['right_weight'],ignition_on_fraction=ignition,dt_next_s=np.r_[np.diff(target),0.0],has_next_state=np.r_[np.ones(len(target)-1,dtype=bool),False],initial_particle_xyz_m=initial_xyz)
 meta={'case':case,'source_case':raw_case,'split':c['split'],'static_inputs':static,'geometry':{k:g[k] for k in ['cones','ellipsoids','stems']},'domain_m':domain,'tree_center_xy_m':center.tolist(),'mesh_spacing_m':dx,'state_names':NAMES,'state_units':UNITS,'raw_archive_sha256':source.get('sha256'),'raw_restoration_receipt_sha256':sha(Path(source['restoration_receipt'])) if source.get('restoration_receipt') else None,'raw_input_sha256':hashes,'selected_particle_classes':[ids[i] for i in selected],'initial_class_wet_masses_kg':class_masses,'cone_fit':fit,'training_npz_sha256':sha(dest/'training.npz'),'initial_mass_matches_deck_design':True,'frames':len(target),'source_temperature_frames':len(times),'cone_interpolation':'Piecewise linear in actual source time; zero geometry when absent; presence between0 and1 is synthetic, not probability; no extrapolation.','four_state_definitions':'Water: initial dry-basis moisture mass minus right-endpoint integral of MLR_WATER VAPOR. Unreacted fuel: initial dry mass minus trapezoidal integral of all vegetation/stem fuel-vapor devices divided by0.75. Gas: summed device fuel-vapor release. Heating: particle mass-weighted surface-temperature excess above20C divided by initial wet mass; K, not energy. No clamping. CSV-integrated channels evaluated at actual particle timestamps.','limitations':'Generic vegetation fuel and species-inspired geometry, not calibrated species. .5m grid; imposed .4m contact patch1500C for20s plus.1s ramps, combustion source HRRPUA60kW/m2 on contact particles. No embers/bark/grass/resolved solid trunk. Woody stems are thermal particles. Hot-gas cone fits >50C cells with>=95% recall, tilt restricted to downwind x-z plane, apex searched on tree axis; not a physical flame boundary. Interpolation cannot recover rapid dynamics or peaks. Original six samples retained. Char oxidation exists in raw physics; unreacted-fuel estimate does not measure total remaining solid mass. Fixed geometry outlines are display context, not burn masks.','conversion':'No model fitting/training; deterministic raw-data extraction and geometric cone fitting.'}
 (dest/'metadata.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n')
 with (dest/'training.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['time_s',*[n+' ['+u+']' for n,u in zip(NAMES,UNITS)],'cone_observed','cone_left_time_s','cone_right_time_s','cone_right_weight'])
  for j,t in enumerate(target):w.writerow([t,*state[j],bool(interp['observed'][j]),times[interp['left_source_index'][j]],times[interp['right_source_index'][j]],interp['right_weight'][j]])
 sample={'case':case,'fixed_initial_conditions':static,'state_names':NAMES,'state_units':UNITS,'initial_state':{'time_s':float(target[0]),'values':state[0].tolist(),'cone_observed':bool(interp['observed'][0])},'next_state':{'time_s':float(target[1]),'values':state[1].tolist(),'cone_observed':bool(interp['observed'][1]),'cone_source_times_s':[times[interp['left_source_index'][1]],times[interp['right_source_index'][1]]],'cone_right_weight':float(interp['right_weight'][1])},'step_inputs':{'dt_s':float(target[1]-target[0]),'ignition_on_fraction_at_initial':float(ignition[0]),'ignition_on_fraction_at_next':float(ignition[1]),'ignition_schedule_s_fraction':[[0,0],[.1,1],[20,1],[20.1,0]]},'provenance':{'raw_archive_sha256':source.get('sha256'),'raw_restoration_receipt_sha256':sha(Path(source['restoration_receipt'])) if source.get('restoration_receipt') else None,'training_npz_sha256':meta['training_npz_sha256'],'no_historical_state_window':True,'cone_values_between_saved_times_are_interpolated':True}}
 (dest/'first-transition.json').write_text(json.dumps(sample,indent=2,allow_nan=False)+'\n')
 lines=[f'# {case}: first transition','',f'Actual times: {target[0]:.9f} -> {target[1]:.9f} s. Next cone values are interpolated, not measured.','', 'Fixed inputs:','', '```json',json.dumps(static,indent=2),'```','', '| State | Units | Initial | Next |','|---|---|---:|---:|']
 lines += [f'| {n} | {u} | {state[0,i]:.9g} | {state[1,i]:.9g} |' for i,(n,u) in enumerate(zip(NAMES,UNITS))]
 lines += ['', 'No hidden historical state window. Water/fuel are integral estimates; heating is a temperature-weighted index, not energy. Cone is a fitted hot-gas envelope, not a flame surface.','',meta['cone_interpolation']]
 (dest/'first-transition.md').write_text('\n'.join(lines)+'\n')
 print('EXTRACTED',case,'frames',len(target),'cone samples',len(times),'max heating',four[:,3].max(),flush=True)
 return dest

def render(dest):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Ellipse,Polygon
 from PIL import Image
 meta=json.loads((dest/'metadata.json').read_text());d=np.load(dest/'training.npz');t=d['time_s'];state=d['state'];assert sha(dest/'training.npz')==meta['training_npz_sha256']
 fig=plt.figure(figsize=(11,7),dpi=90);grid=fig.add_gridspec(4,2,width_ratios=[1.15,1],hspace=.6);ax=fig.add_subplot(grid[:,0]);panels=[fig.add_subplot(grid[i,1]) for i in range(4)]
 center=np.array(meta['tree_center_xy_m']);domain=meta['domain_m'];g=meta['geometry'];static=meta['static_inputs']
 ax.set(xlim=(0,domain[0]),ylim=(0,domain[2]),xlabel='downwind x (m)',ylabel='height z (m)');ax.set_aspect('equal')
 for x,y,z,rx,ry,rz in g['ellipsoids']:ax.add_patch(Ellipse((x+center[0],z),2*rx,2*rz,fill=False,ec='#698b74',lw=1.2))
 for x,y,b,h,r in g['cones']:ax.add_patch(Polygon([[center[0]+x-r,b],[center[0]+x+r,b],[center[0]+x,h]],fill=False,ec='#698b74'))
 for a,b,r in g['stems']:ax.plot([a[0]+center[0],b[0]+center[0]],[a[2],b[2]],c='#755b48',lw=2)
 ig=static['ignition_contact_relative_xyz_m'];marker,=ax.plot([center[0]+ig[0]],[ig[2]],'*',ms=10,color='red')
 cone=Polygon([[0,0],[0,0],[0,0]],color='#ef8c32',alpha=.35);ax.add_patch(cone)
 ax.text(.01,.01,'Side view: fixed geometry outline\nOrange: fitted >50 C hot-gas envelope\nRed star: imposed ignition (while on)',transform=ax.transAxes,fontsize=8,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
 names=['Water estimate','Unreacted fuel estimate','Fuel-gas release','Surface heating index'];dots=[];labels=[]
 for i,p in enumerate(panels):
  p.plot(t,state[:,i],color='#bec8d4',lw=1);dot,=p.plot([],[],'o',color='#205d8e',ms=5);dots.append(dot);p.set(xlim=(0,180),ylabel=UNITS[i]);p.set_title(names[i],fontsize=10,loc='left');p.grid(alpha=.2);labels.append(p.text(.98,.8,'',transform=p.transAxes,ha='right',fontsize=9))
 for panel in panels:panel.ticklabel_format(axis='y',style='plain',useOffset=False)
 panels[-1].set_xlabel('simulation time (s)');title=fig.suptitle('',fontsize=12);fig.subplots_adjust(top=.86,bottom=.13,left=.07,right=.97)
 boundary_note=('Source hot gas reaches domain edges; broad cones include cool air.' if any(f.get('hot_boundary_cells',0)>0 for f in meta['cone_fit']) else 'No active cone in the six saved volumes; earlier/intermediate transients remain unresolved.')
 fig.text(.5,.035,'Training-data rows, not predictions. Six observed cone fits; intermediate cone values are linear interpolation.\n'+boundary_note,ha='center',fontsize=8)
 def update(j):
  row=state[j];present,h,tilt,length,radius,peak=row[4:];u=axis(tilt)[[0,2]];v=np.array([u[1],-u[0]]);tip=np.array([center[0],h]);end=tip+u*length
  cone.set_xy([tip,end+v*radius,end-v*radius]);cone.set_visible(present>0);cone.set_alpha(.35*present);marker.set_visible(d['ignition_on_fraction'][j]>0)
  status='OBSERVED cone fit' if d['cone_observed'][j] else 'INTERPOLATED cone'
  peak_label=f'peak {peak:.1f} C' if present>0 else 'inactive cone (zeros are sentinels)'
  title.set_text(f"{meta['case']} | {static['tree_family']} {static['total_height_m']} m\nt = {t[j]:.3f} s | {status} | {peak_label}")
  for i in range(4):dots[i].set_data([t[j]],[row[i]]);labels[i].set_text(f'{row[i]:.4g} {UNITS[i]}')
 update(0);fig.savefig(dest/'first-frame.png');update(18);fig.savefig(dest/'preview-frame.png')
 images=[]
 for j in range(len(t)):
  update(j);fig.canvas.draw();images.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert('RGB'))
 images[0].save(dest/'training-animation.gif',save_all=True,append_images=images[1:],duration=167,loop=0,optimize=False)
 plt.close(fig)
 verification={'passed':True,'frames':len(t),'training_npz_sha256':sha(dest/'training.npz'),'rendered_row_indices':list(range(len(t))),'rendered_time_s':t.tolist(),'rendered_state_sha256':hashlib.sha256(state.tobytes()).hexdigest(),'no_predicted_or_between_row_frames':True,'playback_fps':6,'physical_time_not_wall_playback':True}
 (dest/'animation-verification.json').write_text(json.dumps(verification,indent=2)+'\n');print('RENDERED',meta['case'],flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--sources',type=Path,default=R/'training-preview-sources.json');ap.add_argument('--render-only',action='store_true');a=ap.parse_args();out=R/'data/training-preview';out.mkdir(exist_ok=True)
 sources=json.loads(a.sources.read_text());assert len(sources)==2
 for s in sources:
  dest=out/s['case'] if a.render_only else extract(s,out)
  render(dest)
