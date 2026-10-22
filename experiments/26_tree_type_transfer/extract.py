"""Extract spatial particle states from raw FDS evidence; never auto-open tests."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from scipy.io import FortranFile,FortranEOFError
from scipy.spatial import cKDTree
from build import ROOT,CLASSES,MODELS

def frames(path):
 f=FortranFile(path);f.read_ints();f.read_ints();nc=int(f.read_ints()[0]);labels=[];units=[]
 for _ in range(nc):
  n=int(f.read_ints()[0]);l=[];u=[]
  for _ in range(n):l.append(f.read_record('u1').tobytes().decode().strip());u.append(f.read_record('u1').tobytes().decode().strip())
  labels.append(l);units.append(u)
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  ps=[]
  for l in labels:
   count=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,count).T;tags=f.read_ints();q=f.read_reals('f4').reshape(len(l),count).T if l else np.zeros((count,0));ps.append((xyz,q,tags))
  yield t,ps,labels,units

def extract(c):
 if c['split'].endswith('test'):
  freeze=ROOT/'results/prediction-freeze.json'
  assert freeze.exists(),'Test outputs forbidden before prediction freeze'
  assert c['case'] in json.loads(freeze.read_text())['cases']
 folder=ROOT/'data/cloud'/c['case'];templates=json.loads((ROOT/'data/tree-templates.json').read_text());lookups=[];initial=[];coords=[]
 for fuel in CLASSES:
  pts=[];groups=[];m0=[]
  for i,node in enumerate(c['trees']):
   m=MODELS[node['type']]
   for p in templates[node['type']]['particles']:
    if p['fuel']!=fuel:continue
    pts.append([p['xyz'][0]+node['x'],p['xyz'][1]+node['y'],p['xyz'][2]])
    z=min(3,int(4*(p['xyz'][2]-m['base'])/m['height']));g=i*16+(int(p['xyz'][0]>=0)*2+int(p['xyz'][1]>=0))*4+z;groups.append(g)
  lookups.append((cKDTree(np.array(pts)),np.array(groups)));coords.append(pts)
 ng=len(c['trees'])*16;times=[];arrays=[];raw_units=None
 for t,ps,labels,units in frames(folder/(c['case']+'_1.prt5')):
  state=np.zeros((4,ng,6));state[:,:,0]=20
  for k,(xyz,q,tags) in enumerate(ps[:4]):
   assert labels[k][:6]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR','PARTICLE DIAMETER','INCIDENT HEAT FLUX','PARTICLE CONVECTIVE HEAT FLUX'],labels[k]
   tree,group=lookups[k]
   if not len(xyz):continue
   dist,idx=tree.query(xyz);assert dist.max()<1e-5 and len(set(idx))==len(idx)
   g=group[idx];mass=q[:,1]*q[:,2]
   for j in range(ng):
    mask=g==j
    if not mask.any():continue
    # Weight temperatures/fluxes by represented particle count, not changing remaining mass.
    w=q[mask,2];state[k,j]=[np.average(q[mask,0],weights=w),mass[mask].sum(),np.average(q[mask,4],weights=w),np.average(q[mask,5],weights=w),q[mask,0].max(),mask.sum()]
  times.append(t);arrays.append(state);raw_units=units[:4]
 a=np.array(arrays);tt=np.array(times);assert np.all(np.diff(tt)>0)
 out=ROOT/'data/extracted';out.mkdir(exist_ok=True)
 np.savez_compressed(out/(c['case']+'.npz'),time=tt,state=a)
 with (folder/(c['case']+'_devc.csv')).open() as f:
  rows=list(csv.reader(f));keys=[s.strip().strip('"') for s in rows[1]];du=[s.strip().strip('"') for s in rows[0]];dv=np.array([[float(v) for v in row] for row in rows[2:] if row]);devices=dict(zip(keys,dv.T))
 reports=[]
 for i,node in enumerate(c['trees']):
  rate=sum(devices[f'v{i} fuel {fuel}'] for fuel in CLASSES);post=dv[:,0]>=c['duration']+1
  unit={du[keys.index(f'v{i} fuel {fuel}')] for fuel in CLASSES};assert unit=={'kg/s'},unit
  reports.append(dict(type=node['type'],initial_wet_mass_kg=float(a[0,:,i*16:(i+1)*16,1].sum()),final_wet_mass_kg=float(a[-1,:,i*16:(i+1)*16,1].sum()),peak_particle_temperature_C=float(a[:,:,i*16:(i+1)*16,4].max()),fuel_release_after_heater_kg=float(np.trapezoid(rate[post],dv[post,0])),peak_post_heater_fuel_rate_kg_s=float(rate[post].max()) if post.any() else None))
 result=dict(case=c['case'],split=c['split'],physical_end_s=float(tt[-1]),nodes_per_fuel=ng,particle_units=raw_units,canopies=reports,state_channels=['represented-count-weighted surface temperature C','remaining wet+solid mass kg','incident radiation kW/m2','convective flux kW/m2','max particle surface temperature C','computational particle count'],warning='Mass loss is not fuel-vapor release: includes water/solid chemistry. Class fuel-release devices are the emission evidence. No FDS incoming flux permitted at autonomous inference.')
 (out/(c['case']+'.json')).write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);args=p.parse_args();c=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['case']==args.case);print(json.dumps(extract(c),indent=2))
