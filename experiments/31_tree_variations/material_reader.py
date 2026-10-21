"""Extract development-only material states and frozen input geometry from raw particles."""
from pathlib import Path
import json,hashlib,csv,io,tarfile
import numpy as np
from scipy.io import FortranFile,FortranEOFError
R=Path(__file__).parent;P=R.parent/'27_single_tree_cnn'
def frames(path):
 f=FortranFile(path);f.read_ints();f.read_ints();nc=int(f.read_ints()[0]);labels=[]
 for _ in range(nc):
  n=int(f.read_ints()[0]);l=[]
  for _ in range(n):l.append(f.read_record('u1').tobytes().decode().strip());f.read_record('u1')
  labels.append(l)
 while True:
  try:t=float(f.read_reals('f4')[0])
  except FortranEOFError:break
  ps=[]
  for l in labels:
   n=int(f.read_ints()[0]);xyz=f.read_reals('f4').reshape(3,n).T;tag=f.read_ints();q=f.read_reals('f4').reshape(len(l),n).T if l else None;ps.append((xyz,q))
  yield t,ps,labels

def main():
 cs=json.loads((R/'cases.json').read_text());reports=[];initial=None
 for c in cs:
  assert c['split'] in ['train','validation'];path=P/'data/cloud'/c['case']/(c['case']+'_1.prt5');times=[];mass=[];temperature=[];geom=None
  for t,ps,labels in frames(path):
   if sum(len(x) for x,q in ps[:4])==0:continue
   m=np.zeros((4,12,8,8),np.float32);temp=np.zeros_like(m);g=np.zeros((4,48,32,32),np.float32)
   for k,(x,q) in enumerate(ps[:4]):
    assert labels[k][:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR'];idx=np.minimum((x/2).astype(int),[11,7,7]);mm=q[:,1]*q[:,2];np.add.at(m[k],tuple(idx.T),mm);np.add.at(temp[k],tuple(idx.T),mm*q[:,0]);ix=np.minimum((x/.5).astype(int),[47,31,31]);np.add.at(g[k],tuple(ix.T),mm/.125)
   temp=np.divide(temp,m,out=np.full_like(temp,20),where=m>0)
   if geom is None:geom=g.copy()
   times.append(t);mass.append(m);temperature.append(temp)
  tt=np.array(times);mm=np.array(mass);temp=np.array(temperature);wanted=np.load(R.parent/'29_single_tree_heads/data/fields'/(c['case']+'-time.npy'));ids=np.abs(tt[:,None]-wanted).argmin(0)
  assert np.max(np.abs(tt[ids]-wanted))<.11
  if initial is None:initial=geom
  assert np.max(abs(initial-geom))<1e-4,'Tree instances or initial mass differ'
  np.savez_compressed(R/'data'/(c['case']+'-material.npz'),mass=mm[ids],temperature=temp[ids],time=wanted)
  reports.append(dict(case=c['case'],raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),first_particle_time=float(tt[0]),initial_mass_kg=mm[0].sum((1,2,3)).tolist(),max_positive_mass_increment_kg=float(np.diff(mm,axis=0).max()),last_mass_kg=float(mm[-1].sum())))
 np.save(R/'data/geometry.npy',initial);(R/'results/material-audit.json').write_text(json.dumps(reports,indent=2));print('Extracted',len(reports),'cases, initial total kg',float(initial.sum()*.125))
if __name__=='__main__':main()
