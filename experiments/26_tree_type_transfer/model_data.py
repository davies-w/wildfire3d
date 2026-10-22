"""Build graph descriptors from frozen INPUTS; load observations only by split."""
import json,math,csv
import numpy as np
import torch
from build import ROOT,MODELS,CLASSES

def geometry(c):
 templates=json.loads((ROOT/'data/tree-templates.json').read_text());static=[];xyz=[];inst=[];fuel=[];indices=[]
 sav=[3940.,2667.,888.,500.];length=[.05,.1,.1,.1]
 for k,klass in enumerate(CLASSES):
  for i,t in enumerate(c['trees']):
   m=MODELS[t['type']];groups=[[] for _ in range(16)]
   for p in templates[t['type']]['particles']:
    if p['fuel']!=klass:continue
    z=min(3,int(4*(p['xyz'][2]-m['base'])/m['height']));g=(int(p['xyz'][0]>=0)*2+int(p['xyz'][1]>=0))*4+z;groups[g].append(p)
   for g,pts in enumerate(groups):
    if not pts:continue
    weights=np.array([p['weight'] for p in pts]);local=np.average([p['xyz'] for p in pts],axis=0,weights=weights)
    radius=2/sav[k];mass=weights.sum()*math.pi*radius**2*length[k]*500*1.12
    area=weights.sum()*2*math.pi*radius*length[k]
    v=math.pi*m['r']**2*m['height']/(3 if m['shape']=='cone' else 1)/16
    # Area is nominal lateral cylindrical area, not an inferred measured flux.
    static.append([float(j==k) for j in range(4)]+[m['r']/3,m['height']/10,local[0]/3,local[1]/3,(local[2]-m['base'])/10,mass,area/100,v/10])
    xyz.append([local[0]+t['x'],local[1]+t['y'],local[2]]);inst.append(i);fuel.append(k);indices.append(k*len(c['trees'])*16+i*16+g)
 return dict(static=torch.tensor(static,dtype=torch.float32),xyz=torch.tensor(xyz,dtype=torch.float32),instance=torch.tensor(inst),fuel=torch.tensor(fuel),indices=np.array(indices),heater_xyz=torch.tensor([*c['heater_xy'],2.1],dtype=torch.float32))

def observation(c):
 assert c['split'] in ['train','validation'],'Training loader cannot open any test output'
 g=geometry(c);a=np.load(ROOT/'data/extracted'/(c['case']+'.npz'));time=a['time'];raw=a['state'].reshape(len(time),-1,6)[:,g['indices']]
 m0=g['static'][:,9].numpy();assert np.max(abs(raw[0,:,1]/m0-1))<.002
 state=np.stack([(raw[:,:,0]-20)/1000,raw[:,:,1]/m0],-1)
 heat=raw[:,:,[2,3]]
 folder=ROOT/'data/cloud'/c['case']
 with (folder/(c['case']+'_devc.csv')).open() as f:r=list(csv.reader(f))
 keys=[s.strip().strip('"') for s in r[1]];dv=np.array([[float(v) for v in row] for row in r[2:] if row]);rates=[]
 for i in range(len(c['trees'])):
  rates.append([np.interp(time,dv[:,0],dv[:,keys.index(f'v{i} fuel {klass}')]) for klass in CLASSES])
 g.update(case=c,state=torch.tensor(state,dtype=torch.float32),heat=torch.tensor(heat,dtype=torch.float32),rates=torch.tensor(np.array(rates).transpose(2,0,1),dtype=torch.float32),time=time,schedule=[c['strength'] if t+1<c['duration'] else 0. for t in time[:-1]])
 return g

if __name__=='__main__':
 cs=json.loads((ROOT/'cases.json').read_text())
 for c in cs:
  g=geometry(c);assert g['static'].shape[1]==12 and torch.isfinite(g['static']).all()
 print('Input-only graph descriptors verified for',len(cs),'cases; no simulation outputs read')
