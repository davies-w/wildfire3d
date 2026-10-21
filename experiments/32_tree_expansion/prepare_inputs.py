"""Prepare input-only descriptors and reuse existing development data; no fresh test outputs."""
from pathlib import Path
import json,shutil
import numpy as np
from material_reader import frames
R=Path(__file__).parent;S=R.parent/'31_tree_variations';P=R.parent/'27_single_tree_cnn';T=R.parent/'30_tree_sequence'
def main():
 cases=json.loads((R/'cases.json').read_text());templates=json.loads((R/'data/tree-templates.json').read_text());reuse=json.loads((R/'reuse.json').read_text());old={c['case']:c for c in json.loads((S/'development.json').read_text())}
 reference=next(ps for t,ps,labels in frames(P/'data/cloud/s27_train_0/s27_train_0_1.prt5') if len(ps[0][0]));dry=[float(q[0,1])/1.12 for x,q in reference[:4]];fuels=['foliage','small roundwood','medium roundwood','large roundwood'];geoms={};rows=[]
 for c in cases:
  g=np.zeros((4,48,32,32),np.float32)
  for k,fuel in enumerate(fuels):
   ps=[p for p in templates[c['geometry_key']]['A']['particles'] if p['fuel']==fuel];x=np.array([p['xyz'] for p in ps])+[8,8,0];weight=np.array([p['weight'] for p in ps]);ix=(x/.5).astype(int);np.add.at(g[k],tuple(ix.T),weight*dry[k]*(1+c['moisture'])/.125)
  geoms[c['case']]=g
  if c['split']!='test':rows.append(dict(c,new_geometry=True))
 oldgeom=dict(np.load(S/'data/geometries.npz'))
 for c in reuse:
  n=c['case'];row=dict(old[n],moisture=.12,configuration=n,new_geometry=False,seed=4321);assert row['split']==c['split'];rows.append(row);geoms[n]=oldgeom[n];shutil.copy2(S/'data'/(n+'-material.npz'),R/'data'/(n+'-material.npz'))
  if n.startswith('v31_'):
   (R/'data/fields').mkdir(exist_ok=True)
   for suffix in ['.npy','-time.npy']:shutil.copy2(S/'data/fields'/(n+suffix),R/'data/fields'/(n+suffix))
 np.savez_compressed(R/'data/geometries.npz',**geoms);(R/'development.json').write_text(json.dumps(rows,indent=2));(R/'fresh-tests.json').write_text(json.dumps([dict(c,new_geometry=True) for c in cases if c['split']=='test'],indent=2));(R/'data/models').mkdir(exist_ok=True)
 shutil.copy2(T/'data/cloud/sequence.pt',R/'data/models/sequence_stage1.pt');shutil.copy2(S/'data/models/geometry_snapshot.pt',R/'data/models/previous.pt')
 print('Prepared',len(rows),'development trajectories and',len(cases)-424,'input-only test descriptors')
if __name__=='__main__':main()
