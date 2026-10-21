"""Build development data and geometry descriptors; never opens fresh test outputs."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from fields import extract
from material_reader import frames
R=Path(__file__).parent;O=R.parent/'29_single_tree_heads';S=R.parent/'30_tree_sequence';P=R.parent/'27_single_tree_cnn'
def main():
 new=json.loads((R/'cases.json').read_text());old=json.loads((O/'cases.json').read_text());geom={};initial=np.load(S/'data/geometry.npy');fuels=['foliage','small roundwood','medium roundwood','large roundwood'];reference=next(ps for t,ps,labels in frames(P/'data/cloud/s27_train_0/s27_train_0_1.prt5') if len(ps[0][0]));particle_mass=[]
 for x,q in reference[:4]:assert np.ptp(q[:,1])<1e-7;particle_mass.append(float(q[0,1]))
 expected=json.loads((R/'data/expected-particles.json').read_text());allrows=[];audits=[]
 for c in old:
  assert c['split'] in ['train','validation'];geom[c['case']]=initial;allrows.append(dict(c,new_geometry=False));shutil.copy2(S/'data'/(c['case']+'-material.npz'),R/'data'/(c['case']+'-material.npz'))
 for c in new:
  name=c['case'];g=np.zeros((4,48,32,32),np.float32)
  for k,fuel in enumerate(fuels):
   ps=[p for p in expected[name] if p['fuel']==fuel];x=np.array([p['xyz'] for p in ps]);w=np.array([p['weight'] for p in ps]);idx=(x/.5).astype(int);np.add.at(g[k],tuple(idx.T),w*particle_mass[k]/.125)
  geom[name]=g
  if c['split']=='test':continue
  result=json.loads((R/'data/cloud'/name/'result.json').read_text());assert result['full_horizon'];extract(c);times=[];mass=[];temp=[];actual=None
  for t,ps,labels in frames(R/'data/cloud'/name/(name+'_1.prt5')):
   if not len(ps[0][0]):continue
   mm=np.zeros((4,12,8,8),np.float32);tt=np.zeros_like(mm);ag=np.zeros_like(g)
   for k,(x,q) in enumerate(ps[:4]):
    ix=(x/2).astype(int);m=q[:,1]*q[:,2];np.add.at(mm[k],tuple(ix.T),m);np.add.at(tt[k],tuple(ix.T),m*q[:,0]);ig=(x/.5).astype(int);np.add.at(ag[k],tuple(ig.T),m/.125)
   if actual is None:actual=ag
   times.append(t);mass.append(mm);temp.append(np.divide(tt,mm,out=np.full_like(tt,20),where=mm>0))
  err=float(abs(actual-g).max());assert err<1e-4,(name,err);wanted=np.load(R/'data/fields'/(name+'-time.npy'));times=np.array(times);ids=abs(times[:,None]-wanted).argmin(0);assert max(abs(times[ids]-wanted))<.11
  np.savez_compressed(R/'data'/(name+'-material.npz'),mass=np.array(mass)[ids],temperature=np.array(temp)[ids],time=wanted);allrows.append(dict(c,new_geometry=True));audits.append(dict(case=name,descriptor_max_density_error_kg_m3=err,initial_mass_kg=float(g.sum()*.125),raw_particle_sha256=hashlib.sha256((R/'data/cloud'/name/(name+'_1.prt5')).read_bytes()).hexdigest()))
 np.savez_compressed(R/'data/geometries.npz',**geom);(R/'development.json').write_text(json.dumps(allrows,indent=2));(R/'fresh-tests.json').write_text(json.dumps([dict(c,new_geometry=True) for c in new if c['split']=='test'],indent=2));(R/'results/learning-data-audit.json').write_text(json.dumps(audits,indent=2));(R/'data/models').mkdir(exist_ok=True);shutil.copy2(S/'data/cloud/sequence.pt',R/'data/models/sequence_stage1.pt');print('Prepared',len(allrows),'development cases, 2 test geometry descriptors; no test outputs accessed')
if __name__=='__main__':main()
