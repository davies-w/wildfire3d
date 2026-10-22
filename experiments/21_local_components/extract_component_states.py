"""Local time-series labels from raw FDS particles/devices, not whole-scene labels."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
from scipy.io import FortranFile,FortranEOFError
from scene import ROOT,CLASSES

def devices(folder,name):
 with (folder/(name+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[v.strip().strip('"') for v in next(r)];a=np.array([list(map(float,v)) for v in r if v]);return dict(zip(keys,a.T))

def extract(c,folder=None):
 name=c['case'];folder=Path(folder) if folder else ROOT/'data/cloud'/name
 d=devices(folder,name);device_mid=(d['Time'][1:]+d['Time'][:-1])/2;f=FortranFile(folder/(name+'_1.prt5'));assert int(f.read_ints()[0])==1;version=int(f.read_ints()[0]);nc=int(f.read_ints()[0]);labels=[]
 for _ in range(nc):
  nq=int(f.read_ints()[0]);q=[]
  for j in range(nq):q.append(bytes(f.read_record('u1')).decode().strip());f.read_record('u1')
  labels.append(q)
 required=['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX']
 assert all(all(k in labels[i] for k in required) for i in range(4)),labels
 records=[];ignitors=[]
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  frame=[dict(id=n['id'],classes=[]) for n in c['canopies']]
  for cls in range(nc):
   count=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,count);f.read_ints();q=f.read_reals('f4').reshape(len(labels[cls]),count) if labels[cls] else None
   if cls==4:ignitors.append([t,count])
   if cls>=4:continue
   vals={k:q[labels[cls].index(k)] for k in required};assigned=np.zeros(count,dtype=int)
   for i,n in enumerate(c['canopies']):
    # FDS cone voxelization is cell-centre based: bounding-box assignment avoids falsely discarding jittered edge particles.
    mask=(abs(xyz[0]-n['x'])<=n['radius']+.01)&(abs(xyz[1]-n['y'])<=n['radius']+.01)&(xyz[2]>=n['base']-.01)&(xyz[2]<=n['base']+n['height']+.01);assigned+=mask
    weight=vals['PARTICLE WEIGHTING FACTOR'][mask];mass=vals['PARTICLE MASS'][mask]*weight
    diameter=vals['PARTICLE DIAMETER'][mask]*1e-6 # FDS reports micrometres; cylindrical lateral area from class LENGTH.
    length=[.05,.10,.10,.10][cls];area=np.pi*diameter*length*weight
    temp=vals['PARTICLE TEMPERATURE'][mask]
    def avg(key):return float(np.average(vals[key][mask],weights=area)) if area.sum()>0 else 0.
    frame[i]['classes'].append(dict(fuel=CLASSES[cls][0],represented_mass_kg=float(mass.sum()),represented_area_m2=float(area.sum()),temperature_mass_mean_C=float(np.average(temp,weights=mass)) if mass.sum()>0 else 20.,temperature_p95_C=float(np.quantile(temp,.95)) if len(temp) else 20.,temperature_max_C=float(temp.max()) if len(temp) else 20.,mass_above300_kg=float(mass[temp>=300].sum()),mass_above500_kg=float(mass[temp>=500].sum()),incident_radiation_area_mean_kw_m2=avg('INCIDENT HEAT FLUX'),convection_area_mean_kw_m2=avg('PARTICLE CONVECTIVE HEAT FLUX')))
   assert np.all(assigned==1) if count else True, f'{name}: ambiguous/unassigned particles at{t},class{cls}'
  for i,n in enumerate(c['canopies']):
   total=sum(v['represented_mass_kg'] for v in frame[i]['classes']);dev=sum(float(np.interp(t,device_mid,v[1:])) for k,v in d.items() if k.startswith(n['id']+' mass '));frame[i]['device_mass_kg']=dev;frame[i]['mass_discrepancy_kg']=total-dev
   frame[i]['fuel_release_kg_s']=sum(float(np.interp(t,device_mid,v[1:])) for k,v in d.items() if k.startswith(n['id']+' fuel '))
  records.append(dict(time_s=t,canopies=frame))
 facade=[]
 for key in d:
  if key.startswith('p') and key.endswith('_temp'):
   stem=key[:-5];y,z=map(float,stem[1:].split('_'));facade.append(dict(id=stem,xyz=[c['facade']['x'],y,z],normal=[-1,0,0],time_s=device_mid.tolist(),temperature_C=d[key][1:].tolist(),incident_radiation_kw_m2=d[stem+'_rad_in'][1:].tolist(),convection_kw_m2=d[stem+'_conv'][1:].tolist(),burning_kg_m2_s=d[stem+'_burn'][1:].tolist()))
 for patch in c.get('extra_surface_patches',[]):
  stem=patch['id'];facade.append(dict(patch,time_s=device_mid.tolist(),temperature_C=d[stem+'_temp'][1:].tolist(),incident_radiation_kw_m2=d[stem+'_rad_in'][1:].tolist(),convection_kw_m2=d[stem+'_conv'][1:].tolist(),burning_kg_m2_s=d[stem+'_burn'][1:].tolist()))
 return dict(case=name,split=c['split'],configuration=c,particle_labels=labels,particle_frames=records,facade=facade,ignitors=ignitors,raw_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [folder/(name+'_devc.csv'),folder/(name+'_1.prt5')]},semantics='Device values are interval averages located at interval midpoints as an approximation, not instantaneous samples; particle snapshots are instantaneous. Particle mass multiplied by representative weight. Incident radiation is incoming, convection signed; no net-radiation substitution. Temperatures aggregate distributions, not uniform physical crowns. P95 is particle-sample quantile, not mass-weighted. Bounding boxes assign non-overlapping crowns; mass reconciliation must be checked before training.')

def main():
 import sys
 rows=json.loads((ROOT/'component-development.json').read_text())['cases'];out=ROOT/'data/component_states';out.mkdir(exist_ok=True)
 for name in sys.argv[1:]:
  c=next(c for c in rows if c['case']==name);r=extract(c);(out/(name+'.json')).write_text(json.dumps(r));print('EXTRACTED',name,'frames',len(r['particle_frames']))
def preflight():
 rows=json.loads((ROOT/'component-development.json').read_text())['cases'];checks=[]
 for name in ['b21_single_0','b21_transfer_1','b21_combined_1','b21_corner_1']:
  c=next(c for c in rows if c['case']==name);r=extract(c,ROOT/'data/component_preflight'/name)
  errors=[abs(n['mass_discrepancy_kg']) for f in r['particle_frames'] if f['time_s']>=.5 for n in f['canopies']]
  assert errors and max(errors)<.001
  checks.append(dict(case=name,frames=len(r['particle_frames']),facade_patches=len(r['facade']),max_mass_discrepancy_kg=max(errors)))
 (ROOT/'results/component-extraction-preflight.json').write_text(json.dumps(checks,indent=2))
if __name__=='__main__':
 import sys
 preflight() if sys.argv[1:]==['--preflight'] else main()

