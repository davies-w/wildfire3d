from preview_training import solve_folder,source_case
"""User-requested anchored-cone versus free-cone comparison, two cases only."""
import json, shutil, csv
import numpy as np
from preview_training import R,sha
from spatial_training_variants import CASES
OUT=R/'data/cone-comparison-preview'
BASE=R/'data/spatial-training-variants'
REPORT=R/'data/pivot-investigation/report.json'
def generate(case):
 root=OUT/case;root.mkdir(parents=True,exist_ok=True)
 prior=BASE/case
 shutil.copytree(prior/'cone',root/'cone',dirs_exist_ok=True)
 shutil.copy2(prior/'observed-hot-cells.json',root/'observed-hot-cells.json')
 old=np.load(root/'cone/training.npz');meta=json.loads((root/'cone/metadata.json').read_text())
 report=json.loads(REPORT.read_text());frames=next(x['frames'] for x in report['cases'] if x['case']==case)
 src=[]
 for f in frames:
  if not f.get('fits'):src.append(np.zeros(10));continue
  c=f['fits']['plus_horizontal_apex'];tilt,az=np.deg2rad([c['tilt_deg'],c['azimuth_deg']]);u=[np.sin(tilt)*np.cos(az),np.sin(tilt)*np.sin(az),np.cos(tilt)]
  # Peak is independently recomputed below from the original raw volume.
  src.append(np.r_[1,c['apex_m'],u,c['length_m'],c['radius_m'],0])
 from preview_training import temperatures
 raw=(solve_folder(case)/(source_case(case)+'_1_1.sf'))
 assert sha(raw)==meta['raw_temperature_sha256']
 domain=meta['domain_m'];shape=np.rint(np.array(domain)/.5).astype(int);xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3)
 diagnostics=[]
 for i,(t,a) in enumerate(temperatures(raw,domain,.5)):
  assert t==old['source_time_s'][i];temp=a.reshape(-1);hot=temp>50;row=src[i]
  if not row[0]:assert not hot.any();continue
  d=xyz-row[1:4];ax=d@row[4:7];mask=(ax>=0)&(ax<=row[7]+1e-9)&(np.maximum((d*d).sum(1)-ax*ax,0)<=(row[8]*ax/row[7])**2+1e-9)
  recall=(mask&hot).sum()/hot.sum();assert recall>=.95-1e-9;row[-1]=temp[mask].max();diagnostics.append(dict(time_s=t,hot_recall=float(recall),hot_precision=float((mask&hot).sum()/mask.sum())))
 src=np.array(src);values=[]
 for l,h,w in zip(old['left_source_index'],old['right_source_index'],old['right_weight']):
  a,b=src[l],src[h];v=(1-w)*a+w*b
  if a[0] and b[0]:v[4:7]/=np.linalg.norm(v[4:7])
  elif bool(a[0])!=bool(b[0]):v[1:7]=(a if a[0] else b)[1:7]
  if v[0]==0:v[:]=0
  values.append(v)
 values=np.array(values)
 for i,t in enumerate(old['source_time_s']):values[np.flatnonzero(old['time_s']==t)[0]]=src[i]
 states=np.column_stack([old['state'][:,:4],values]);names=list(old['state_names'][:4])+['presence','apex_x','apex_y','apex_z','axis_x','axis_y','axis_z','axial_length','end_radius','peak_temperature'];units=list(old['state_units'][:4])+['fraction','m','m','m','unitless','unitless','unitless','m','m','degC']
 dest=root/'free_cone';dest.mkdir(exist_ok=True);payload={k:old[k] for k in old.files};payload.update(state=states,state_names=names,state_units=units,source_spatial_state=src);np.savez_compressed(dest/'training.npz',**payload)
 meta['limits']=meta['limits'].replace('anchored tip fixed at ignition location;', 'free tip bounded to the simulation-domain x/y and zero-to-tree-height z;')
 meta.update(variant='free_cone',state_names=names,state_units=units,training_npz_sha256=sha(dest/'training.npz'),method='Free cone from previously reviewed plus_horizontal_apex fit: apex xyz, tilt and azimuth optimized with three deterministic seeds; all-hot-cell extent calibration for >=95% recall. Same bounds as pivot investigation, not a global optimum. Apex is a geometric parameter, not a physical fire origin.',interpolation='Linear apex, extents, presence and peak; normalized-linear unit direction between active observations. During appearance/disappearance hold the active endpoint apex/direction and linearly grow/shrink extents. Absent zeros are sentinels. No extrapolation. Six exact source rows retained.')
 (dest/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 with (dest/'training.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['time_s',*[f'{n} [{u}]' for n,u in zip(names,units)],'spatial_observed']);w.writerows([[t,*v,bool(o)] for t,v,o in zip(old['time_s'],states,old['observed'])])
 sample=json.loads((root/'cone/first-transition.json').read_text());sample.update(variant='free_cone',state_names=names,state_units=units,training_npz_sha256=meta['training_npz_sha256']);sample.pop('cone_anchor_xyz_m',None);sample['initial_state']['values']=states[0].tolist();sample['next_state']['values']=states[1].tolist();(dest/'first-transition.json').write_text(json.dumps(sample,indent=2)+'\n')
 lines=['# Free cone first transition','','| State | Unit | Initial | Next |','|---|---|---:|---:|']+[f'| {n} | {u} | {a:.9g} | {b:.9g} |' for n,u,a,b in zip(names,units,states[0],states[1])];lines+=['','Fixed conditions, actual times and provenance: first-transition.json. Next spatial state is interpolated.']
 (dest/'first-transition.md').write_text('\n'.join(lines)+'\n');(root/'free-cone-fit-validation.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
 assert states.shape==(91,14) and np.isfinite(states).all() and np.array_equal(states[:,:4],old['state'][:,:4])
 for row in values:
  if row[0]:assert abs(np.linalg.norm(row[4:7])-1)<1e-12
 print('VALIDATED',case,flush=True)
def render(case):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from PIL import Image
 root=OUT/case;cloud=json.loads((root/'observed-hot-cells.json').read_text());datasets=[np.load(root/k/'training.npz') for k in ['cone','free_cone']];meta=json.loads((root/'cone/metadata.json').read_text());times=datasets[0]['time_s'];domain=meta['domain_m'];center=meta['tree_center_xy_m'];anchor=np.array(meta['cone_anchor_xyz_m']);geometry=meta['geometry']
 fig=plt.figure(figsize=(12,6),dpi=85);axes=[fig.add_subplot(121,projection='3d'),fig.add_subplot(122,projection='3d')];theta=np.linspace(0,2*np.pi,40);phi=np.linspace(0,np.pi,20);sphere=np.stack([np.outer(np.cos(theta),np.sin(phi)),np.outer(np.sin(theta),np.sin(phi)),np.outer(np.ones_like(theta),np.cos(phi))],-1)
 def draw(j):
  for ax,data,kind in zip(axes,datasets,['cone','free_cone']):
   ax.clear();ax.set(xlim=(0,domain[0]),ylim=(0,domain[1]),zlim=(0,domain[2]),xlabel='x (m)',ylabel='y (m)',zlabel='z (m)');ax.set_box_aspect(domain);ax.view_init(22,-63)
   for a,b,r in geometry['stems']:ax.plot([a[0]+center[0],b[0]+center[0]],[a[1]+center[1],b[1]+center[1]],[a[2],b[2]],c='#6e6855',lw=1)
   for x,y,z,rx,ry,rz in geometry['ellipsoids']:
    pts=sphere*np.array([rx,ry,rz])+np.array([x+center[0],y+center[1],z]);ax.plot_wireframe(pts[:,:,0],pts[:,:,1],pts[:,:,2],rstride=10,cstride=6,color='#64a06e',alpha=.25,lw=.5)
   for x,y,b,h,rad in geometry['cones']:
    rim=np.column_stack([center[0]+x+rad*np.cos(theta),center[1]+y+rad*np.sin(theta),np.full(len(theta),b)])
    ax.plot(*rim.T,color='#64a06e',alpha=.3,lw=.5)
    for k in range(0,len(theta),10):ax.plot(*np.array([[center[0]+x,center[1]+y,h],rim[k]]).T,color='#64a06e',alpha=.3,lw=.5)
   if data['observed'][j]:
    s=int(np.flatnonzero(data['source_time_s']==times[j])[0]);pts=np.array(cloud[s]['xyz_m'])
    if len(pts):ax.scatter(*pts.T,c='#555555',s=2,alpha=.25)
   ax.scatter(*anchor,c='red',marker='*',s=35)
   row=data['state'][j,4:];presence=row[0]
   if presence>0:
    if kind=='cone':
     u=row[1:4];v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);w=np.cross(u,v);rim=anchor+row[4]*u+row[5]*(np.cos(theta)[:,None]*v+np.sin(theta)[:,None]*w);ax.plot(*rim.T,color='#cc7a15',alpha=.8)
     for k in range(0,len(theta),5):ax.plot(*np.array([anchor,rim[k]]).T,color='#cc7a15',alpha=.8,lw=.7)
    else:
     apex=row[1:4];u=row[4:7];v=np.cross(u,[0,1,0]);v/=np.linalg.norm(v);w=np.cross(u,v);rim=apex+row[7]*u+row[8]*(np.cos(theta)[:,None]*v+np.sin(theta)[:,None]*w);ax.plot(*rim.T,color='#147fba',alpha=.8)
     for k in range(0,len(theta),5):ax.plot(*np.array([apex,rim[k]]).T,color='#147fba',alpha=.8,lw=.7)
     ax.scatter(*apex,marker='x',c='#147fba',s=30)
   label='Anchored cone (11 states)' if kind=='cone' else 'Free cone (14 states)';status='SAVED-VOLUME FIT' if data['observed'][j] else 'INTERPOLATED GEOMETRY'
   ax.set_title(f'{label}\n{status}\n'+(f'Presence {presence:.2f}; peak {row[-1]:.0f} C' if presence>0 else 'Absent in source fits (not 0 C)'),fontsize=9)
  fig.suptitle(f'{case} | {meta["static_inputs"]["tree_family"]} | simulation t={times[j]:.3f}s',fontsize=12)
  fig.texts[:]
 fig.subplots_adjust(left=.02,right=.98,bottom=.22,top=.8,wspace=.08)
 fig.text(.5,.06,'Gray dots: actual >50 C cells, shown ONLY at saved-volume times (display subsample).\nWire shapes: training-state geometry, not a temperature field or measured flame surface; red star: fixed ignition location.\nGreen outlines: initial geometry, not burn state. Domain-clipped observations; no unsaved raw frames fabricated.',ha='center',fontsize=8)
 images=[];durations=[]
 for j in range(len(times)):
  draw(j);fig.canvas.draw();im=Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert('RGB');images.append(im);durations.append(750 if datasets[0]['observed'][j] else 100)
  if j==18:im.save(root/'comparison-preview.png')
 images[0].save(root/'comparison-3d.gif',save_all=True,append_images=images[1:],duration=durations,loop=0,optimize=False);plt.close(fig)
 (root/'animation-verification.json').write_text(json.dumps({'frames':len(times),'row_indices':list(range(len(times))),'time_s':times.tolist(),'cone_npz_sha256':sha(root/'cone/training.npz'),'free_cone_npz_sha256':sha(root/'free_cone/training.npz'),'raw_points_only_at_observed_times':True,'display_duration_ms':durations},indent=2)+'\n');print('RENDERED 3D comparison',case,flush=True)


if __name__=='__main__':
 for case in CASES:generate(case);render(case)
