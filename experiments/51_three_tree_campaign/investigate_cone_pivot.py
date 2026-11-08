"""Ablations of cone-fit restrictions on the two reviewed cases; no label replacement."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.optimize import differential_evolution
from preview_training import temperatures,sha,cone_row
R=Path(__file__).resolve().parent;OUT=R/'data/pivot-investigation';OUT.mkdir(parents=True,exist_ok=True)

def fit_candidate(points,p):
 x,y,z,tilt,az=p;t,a=np.deg2rad([tilt,az]);u=np.array([np.sin(t)*np.cos(a),np.sin(t)*np.sin(a),np.cos(t)])
 d=points-np.array([x,y,z]);s=d@u;ok=s>1e-8;k=int(np.ceil(.95*len(points)))
 if ok.sum()<k:return None
 sp=s[ok];length=float(sp.max());radial=np.sqrt(np.maximum((d[ok]*d[ok]).sum(1)-sp*sp,0));radius=float(np.partition(radial/sp,k-1)[k-1]*length)
 return dict(apex_m=[float(x),float(y),float(z)],tilt_deg=float(tilt),azimuth_deg=float(az),length_m=length,radius_m=radius,volume_m3=float(np.pi*radius**2*length/3))
def evaluate(c,xyz,temp):
 p=c['apex_m'];t,a=np.deg2rad([c['tilt_deg'],c['azimuth_deg']]);u=np.array([np.sin(t)*np.cos(a),np.sin(t)*np.sin(a),np.cos(t)]);d=xyz-p;s=d@u;hot=temp>50
 mask=(s>=0)&(s<=c['length_m']+1e-9)&(np.maximum((d*d).sum(1)-s*s,0)<=(c['radius_m']*s/c['length_m'])**2+1e-9)
 n=int((mask&hot).sum());c={**c,'hot_recall':n/int(hot.sum()),'hot_precision':n/int(mask.sum()),'enclosed_cells':int(mask.sum()),'hot_cells':int(hot.sum()),'peak_inside_C':float(temp[mask].max())};assert c['hot_recall']>=.95-1e-9;return c

def search_grid(points,xy,heights,azimuths):
 sample=points if len(points)<=2048 else points[np.sort(np.random.default_rng(3516).choice(len(points),2048,False))]
 candidates=[]
 for h in heights:
  for tilt in range(0,91,10):
   for az in azimuths:
    p=[*xy,h,tilt,az];c=fit_candidate(sample,p)
    if c:candidates.append((c['volume_m3'],p))
 candidates.sort(key=lambda x:x[0]);final=[fit_candidate(points,p) for _,p in candidates[:32]];final=[c for c in final if c]
 return min(final,key=lambda c:c['volume_m3'])

def search_continuous(points,center,height,domain,free_xy=False,free_az=True,expanded=False):
 sample=points if len(points)<=2048 else points[np.sort(np.random.default_rng(3516).choice(len(points),2048,False))]
 bounds=([(-domain[0],2*domain[0]),(-domain[1],2*domain[1])] if free_xy and expanded else [(0,domain[0]),(0,domain[1])] if free_xy else [])+[(0,height),(0,90)]+([(-180,180)] if free_az else [])
 def params(v):
  q=list(v) if free_xy else [*center,*v]
  return q if free_az else q+[0]
 def objective(v):
  c=fit_candidate(sample,params(v));return c['volume_m3'] if c else 1e12
 results=[]
 for seed in [3516,3517,3518]:
  opt=differential_evolution(objective,bounds,seed=seed,popsize=10,maxiter=55,polish=False,tol=.001,workers=1)
  c=fit_candidate(points,params(opt.x))
  if c:results.append(c)
 assert results
 return min(results,key=lambda c:c['volume_m3']),results

def main():
 report={'scope':'Two preview cases; diagnostic only, no training-label replacement. All active source frames examined.','objective':'Smallest analytic circular cone volume with >=95% of >50C cell centres; length remains maximum positive axial distance.','limitations':'Grid ablations recalibrate top32 sample-ranked candidates on all hot cells; continuous search uses three seeds and2048 deterministic ranking samples, then all-cell recalibration. No global optimum claim. Domain clipping and low50C threshold remain. Geometric apex is not an ignition location.','cases':[]}
 for case in ['tree51_001323_baseline','tree51_001336_baseline']:
  meta=json.loads((R/'data/training-preview'/case/'metadata.json').read_text());g={'crown_base_m':meta['static_inputs']['crown_base_height_m'],'total_height_m':meta['static_inputs']['total_height_m']};domain=meta['domain_m'];shape=tuple(np.rint(np.array(domain)/.5).astype(int));center=meta['tree_center_xy_m'];xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3)
  path=next((R/'data/completed07').glob('*/'+case+'/solve/'+case+'_1_1.sf'));assert sha(path)==meta['raw_input_sha256'][path.name]
  rows=[]
  for t,a in temperatures(path,domain,.5):
   temp=a.reshape(-1);points=xyz[temp>50];row={'time_s':t,'hot_cells':len(points)}
   if not len(points):row.update(active=False,pivot_interpretation='Absent; zero placeholder is not a ground-level fitted apex.');rows.append(row);continue
   row.update(active=True,hot_z_quantiles_m=np.quantile(points[:,2],[0,.05,.5,.95,1]).tolist(),hot_xy_mean_m=points[:,:2].mean(0).tolist(),fraction_hot_below_crown=float((points[:,2]<g['crown_base_m']).mean()))
   old,audit=cone_row(xyz,temp,g,center,shape);p=[*center,old[1],old[2],0];fits={'legacy':evaluate(fit_candidate(points,p),xyz,temp)}
   allold=[fit_candidate(points,[*center,h,tilt,0]) for h in np.unique(np.r_[0,np.linspace(g['crown_base_m'],g['total_height_m'],7)]) for tilt in range(0,91,10)];allold=[c for c in allold if c];fits['legacy_exhaustive']=evaluate(min(allold,key=lambda c:c['volume_m3']),xyz,temp)
   fits['dense_height']=evaluate(search_grid(points,center,np.arange(0,g['total_height_m']+.01,.5),[0]),xyz,temp)
   for name,free_xy,free_az in [('continuous_height_tilt',False,False),('plus_azimuth',False,True),('plus_horizontal_apex',True,True)]:
    best,seeds=search_continuous(points,center,g['total_height_m'],domain,free_xy,free_az);fits[name]=evaluate(best,xyz,temp);fits[name]['seed_fits']=seeds
   # One explicit ignition-position comparison, without assuming it must be the plume apex.
   pos=np.array([*center,0])+np.array(meta['static_inputs']['ignition_contact_relative_xyz_m']);ign=search_grid(points,pos[:2],[pos[2]],range(-180,180,15));fits['ignition_apex']=evaluate(ign,xyz,temp)
   best,seeds=search_continuous(points,center,g['total_height_m'],domain,True,True,True);fits['expanded_xy_diagnostic']=evaluate(best,xyz,temp);fits['expanded_xy_diagnostic']['seed_fits']=seeds
   row['fits']=fits;rows.append(row);print(case,round(t,3),{k:round(v['apex_m'][2],2) for k,v in fits.items()},flush=True)
  report['cases'].append({'case':case,'source_temperature_sha256':sha(path),'frames':rows})
  (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS: diagnostic only; preview data unchanged',flush=True)
if __name__=='__main__':main()
