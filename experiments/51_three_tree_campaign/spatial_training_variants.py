from preview_training import solve_folder,source_case
"""Two-case, raw-derived anchored-cone and free-ellipsoid training previews.
No simulations, model training, bulk conversion or raw deletion.
"""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from preview_training import R,temperatures,sha,NAMES,UNITS
OUT=R/'data/spatial-training-variants'
BASE=R/'data/training-preview'
REPORT=R/'data/pivot-investigation/report.json'
CASES=['tree51_001323_baseline','tree51_001336_baseline']
C_NAMES=NAMES[:4]+['presence','axis_x','axis_y','axis_z','axial_length','end_radius','peak_temperature']
C_UNITS=UNITS[:4]+['fraction','unitless','unitless','unitless','m','m','degC']
E_NAMES=NAMES[:4]+['presence','centre_x','centre_y','centre_z','shape_xx','shape_yy','shape_zz','shape_xy','shape_xz','shape_yz','peak_temperature']
E_UNITS=UNITS[:4]+['fraction','m','m','m','m2','m2','m2','m2','m2','m2','degC']

def pack(S):return S[[0,1,2,0,0,1],[0,1,2,1,2,2]]
def matrix(v):
 a,b,c,d,e,f=v;return np.array([[a,d,e],[d,b,f],[e,f,c]])
def metrics(mask,hot):
 hit=int((mask&hot).sum());return {'hot_recall':hit/int(hot.sum()),'hot_precision':hit/int(mask.sum()),'hot_cells':int(hot.sum()),'enclosed_cells':int(mask.sum())}
def interpolate(t,y,q,kind):
 hi=np.searchsorted(t,q,side='right').clip(1,len(t)-1);lo=hi-1;w=(q-t[lo])/(t[hi]-t[lo]);assert w.min()>=0 and w.max()<=1
 out=[]
 for l,h,a in zip(lo,hi,w):
  L=y[l];H=y[h];row=(1-a)*L+a*H
  if L[0]>0 and H[0]>0:
   if kind=='cone':row[1:4]/=np.linalg.norm(row[1:4])
  elif (L[0]>0) != (H[0]>0):
   active=L if L[0]>0 else H;fraction=1-a if L[0]>0 else a
   row[1:4]=active[1:4] # inactive position/direction is undefined, not at the origin
   if kind=='ellipsoid':row[4:10]=active[4:10]*fraction**2 # linearly shrink semiaxes
  if row[0]==0:row[:]=0
  out.append(row)
 observed=np.isin(q,t);out=np.array(out)
 for j in np.flatnonzero(observed):out[j]=y[np.flatnonzero(t==q[j])[0]]
 return out,observed,lo,hi,w

def generate(case,kinds=('cone','ellipsoid')):
 base=BASE/case;m=json.loads((base/'metadata.json').read_text());old=np.load(base/'training.npz');assert sha(base/'training.npz')==m['training_npz_sha256']
 q=old['time_s'];domain=m['domain_m'];shape=tuple(np.rint(np.array(domain)/.5).astype(int));xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3)
 anchor=np.r_[m['tree_center_xy_m'],0]+m['static_inputs']['ignition_contact_relative_xyz_m'];raw=(solve_folder(case)/(source_case(case)+'_1_1.sf'));assert sha(raw)==m['raw_input_sha256'][raw.name]
 ablations=json.loads(REPORT.read_text());oldrows=next(c['frames'] for c in ablations['cases'] if c['case']==case)
 cone=[];ellipsoid=[];times=[];diagnostics=[];clouds=[]
 for j,(t,a) in enumerate(temperatures(raw,domain,.5)):
  assert t==oldrows[j]['time_s'];temp=a.reshape(-1);hot=temp>50;points=xyz[hot];times.append(t)
  ids=np.flatnonzero(hot);keep=ids[np.linspace(0,len(ids)-1,min(2000,len(ids))).astype(int)] if len(ids) else ids
  clouds.append({'time_s':t,'xyz_m':xyz[keep].tolist(),'temperature_C':temp[keep].tolist(),'original_hot_cells':len(ids),'display_subsample_only':True})
  if not len(points):cone.append(np.zeros(7));ellipsoid.append(np.zeros(11));diagnostics.append({'time_s':t,'active':False});continue
  c=oldrows[j]['fits']['ignition_apex'];assert np.allclose(c['apex_m'],anchor)
  tilt,az=np.deg2rad([c['tilt_deg'],c['azimuth_deg']]);u=np.array([np.sin(tilt)*np.cos(az),np.sin(tilt)*np.sin(az),np.cos(tilt)])
  d=xyz-anchor;s=d@u;cmask=(s>=0)&(s<=c['length_m']+1e-9)&(np.maximum((d*d).sum(1)-s*s,0)<=(c['radius_m']*s/c['length_m'])**2+1e-9)
  cone.append(np.r_[1,u,c['length_m'],c['radius_m'],temp[cmask].max()])
  if 'ellipsoid' not in kinds:
   ellipsoid.append(np.zeros(11));diagnostics.append({'time_s':t,'active':True,'cone':metrics(cmask,hot)});continue
  weights=temp[hot]-20;centre=np.average(points,axis=0,weights=weights);delta=points-centre;cov=(delta.T*weights)@delta/weights.sum();ev=np.linalg.eigvalsh(cov);assert ev.min()>0
  dist=np.einsum('ni,ij,nj->n',delta,np.linalg.inv(cov),delta);k=int(np.ceil(.95*len(points)));scale=float(np.partition(dist,k-1)[k-1]);S=cov*scale
  d=xyz-centre;emask=np.einsum('ni,ij,nj->n',d,np.linalg.inv(S),d)<=1+1e-9
  ellipsoid.append(np.r_[1,centre,pack(S),temp[emask].max()]);cm=metrics(cmask,hot);em=metrics(emask,hot);assert min(cm['hot_recall'],em['hot_recall'])>=.95-1e-9
  vals,vec=np.linalg.eigh(S);diagnostics.append({'time_s':t,'active':True,'cone':cm,'ellipsoid':em,'ellipsoid_semiaxes_m':np.sqrt(vals).tolist(),'ellipsoid_axis_columns_xyz':vec.tolist(),'ellipsoid_centre_m':centre.tolist()})
 times=np.array(times);assert np.array_equal(times,old['source_cone_time_s']);root=OUT/case;root.mkdir(parents=True,exist_ok=True)
 (root/'observed-hot-cells.json').write_text(json.dumps(clouds,separators=(',',':'))+'\n')
 (root/'fit-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
 for kind,source,names,units in [('cone',np.array(cone),C_NAMES,C_UNITS),('ellipsoid',np.array(ellipsoid),E_NAMES,E_UNITS)]:
  if kind not in kinds:continue
  values,observed,lo,hi,w=interpolate(times,source,q,kind);states=np.column_stack([old['state'][:,:4],values]);dest=root/kind;dest.mkdir(exist_ok=True)
  assert np.isfinite(states).all() and np.array_equal(states[:,:4],old['state'][:,:4])
  np.savez_compressed(dest/'training.npz',time_s=q,state=states,state_names=names,state_units=units,source_time_s=times,source_spatial_state=source,observed=observed,interpolated=~observed,left_source_index=lo,right_source_index=hi,right_weight=w,ignition_on_fraction=old['ignition_on_fraction'],dt_next_s=old['dt_next_s'],has_next_state=old['has_next_state'])
  metadata={'case':case,'variant':kind,'state_names':names,'state_units':units,'static_inputs':m['static_inputs'],'geometry':m['geometry'],'domain_m':domain,'tree_center_xy_m':m['tree_center_xy_m'],'cone_anchor_xyz_m':anchor.tolist(),'raw_temperature_sha256':sha(raw),'raw_archive_sha256':m['raw_archive_sha256'],'original_four_state_npz_sha256':m['training_npz_sha256'],'training_npz_sha256':sha(dest/'training.npz'),'split':m['split'],'method':('Ignition-anchored circular cone: 10-degree tilt and15-degree azimuth candidate grid, top32 sample-ranked then all-hot-cell calibrated; >=95% hot-cell recall. Direction represented by unit xyz vector, not angle wrap.' if kind=='cone' else 'Temperature-excess-weighted centroid and covariance, scaled to enclose>=95% hot cells. Shape matrix S defines (x-centre)^T inverse(S) (x-centre)<=1. Six independent S entries encode three semiaxes and full orientation without eigenvector sign flips. This is not minimum-volume optimization.'),'interpolation':'Within saved time range only. Linear presence, peak sentinel and cone extents; active-to-active normalized-linear cone direction, linear ellipsoid centre and shape matrix. During appearance/disappearance hold the available active endpoint centre/direction, shrink extents linearly (ellipsoid shape matrix quadratically). This is an explicit synthetic transition rule, not recovered motion. No centre is interpolated from an absent origin. Zero absent peak is a sentinel, not ambient C. Source rows/masks retained.','limits':m['limitations'].replace('tilt restricted to downwind x-z plane, apex searched on tree axis;', 'full 3D direction; anchored tip fixed at ignition location;')}
  (dest/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
  with (dest/'training.csv').open('w') as f:
   writer=csv.writer(f);writer.writerow(['time_s',*[f'{n} [{u}]' for n,u in zip(names,units)],'spatial_observed']);writer.writerows([[t,*state,bool(obs)] for t,state,obs in zip(q,states,observed)])
  sample={'case':case,'variant':kind,'fixed_initial_conditions':m['static_inputs'],'cone_anchor_xyz_m':anchor.tolist() if kind=='cone' else None,'state_names':names,'state_units':units,'initial_state':{'time_s':float(q[0]),'values':states[0].tolist(),'spatial_observed':bool(observed[0])},'next_state':{'time_s':float(q[1]),'values':states[1].tolist(),'spatial_observed':bool(observed[1]),'source_times_s':[float(times[lo[1]]),float(times[hi[1]])],'right_weight':float(w[1])},'dt_s':float(q[1]-q[0]),'ignition_ramp_s_fraction':[[0,0],[.1,1],[20,1],[20.1,0]],'no_hidden_history_window':True,'training_npz_sha256':metadata['training_npz_sha256']}
  (dest/'first-transition.json').write_text(json.dumps(sample,indent=2)+'\n')
 print('GENERATED both variants',case,flush=True)

def render(case):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from PIL import Image
 root=OUT/case;cloud=json.loads((root/'observed-hot-cells.json').read_text());datasets=[np.load(root/k/'training.npz') for k in ['cone','ellipsoid']];meta=json.loads((root/'cone/metadata.json').read_text());times=datasets[0]['time_s'];domain=meta['domain_m'];center=meta['tree_center_xy_m'];anchor=np.array(meta['cone_anchor_xyz_m']);geometry=meta['geometry']
 fig=plt.figure(figsize=(12,6),dpi=85);axes=[fig.add_subplot(121,projection='3d'),fig.add_subplot(122,projection='3d')];theta=np.linspace(0,2*np.pi,40);phi=np.linspace(0,np.pi,20);sphere=np.stack([np.outer(np.cos(theta),np.sin(phi)),np.outer(np.sin(theta),np.sin(phi)),np.outer(np.ones_like(theta),np.cos(phi))],-1)
 def draw(j):
  for ax,data,kind in zip(axes,datasets,['cone','ellipsoid']):
   ax.clear();ax.set(xlim=(0,domain[0]),ylim=(0,domain[1]),zlim=(0,domain[2]),xlabel='x (m)',ylabel='y (m)',zlabel='z (m)');ax.set_box_aspect(domain);ax.view_init(22,-63)
   for a,b,r in geometry['stems']:ax.plot([a[0]+center[0],b[0]+center[0]],[a[1]+center[1],b[1]+center[1]],[a[2],b[2]],c='#6e6855',lw=1)
   for x,y,z,rx,ry,rz in geometry['ellipsoids']:
    pts=sphere*np.array([rx,ry,rz])+np.array([x+center[0],y+center[1],z]);ax.plot_wireframe(pts[:,:,0],pts[:,:,1],pts[:,:,2],rstride=10,cstride=6,color='#64a06e',alpha=.25,lw=.5)
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
     S=matrix(row[4:10]);ev,V=np.linalg.eigh(S);assert ev.min()>0;pts=sphere@(V@np.diag(np.sqrt(ev))).T+row[1:4];ax.plot_wireframe(pts[:,:,0],pts[:,:,1],pts[:,:,2],rstride=4,cstride=3,color='#147fba',alpha=.8,lw=.65);ax.scatter(*row[1:4],marker='x',c='#147fba',s=30)
   label='Anchored cone (11 states)' if kind=='cone' else 'Free ellipsoid (15 states)';status='SAVED-VOLUME FIT' if data['observed'][j] else 'INTERPOLATED GEOMETRY'
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
 (root/'animation-verification.json').write_text(json.dumps({'frames':len(times),'row_indices':list(range(len(times))),'time_s':times.tolist(),'cone_npz_sha256':sha(root/'cone/training.npz'),'ellipsoid_npz_sha256':sha(root/'ellipsoid/training.npz'),'raw_points_only_at_observed_times':True,'display_duration_ms':durations},indent=2)+'\n');print('RENDERED 3D comparison',case,flush=True)

if __name__=='__main__':
 for case in CASES:generate(case);render(case)
