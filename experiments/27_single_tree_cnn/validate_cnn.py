"""Local numerical checks, including learning a known moving Gaussian field (not FDS evidence)."""
import json,time
import numpy as np
import torch
from cnn import CNN,encode,decode,cond,loss,ROOT
rng=np.random.default_rng(27);a=rng.uniform(size=(2,6,3,3,3)).astype('float32');a[:,0]*=1500;a[:,1]*=3000;a[:,2:5]=a[:,2:5]*20-10;a[:,5]*=300
assert np.allclose(a,decode(encode(a,3),3),rtol=2e-6,atol=1e-4)
torch.manual_seed(27);model=CNN();opt=torch.optim.Adam(model.parameters(),lr=.002)
xyz=np.stack(np.meshgrid(np.arange(48)/48,np.arange(32)/32,np.arange(32)/32,indexing='ij'))
conditions=[];targets=[]
for w,angle in [(1,0),(2,90),(4,180),(5,270)]:
 c=dict(wind_speed=w,angle_deg=angle);conditions.append(cond(c,np.array([60.]))[0]);v=np.zeros((6,48,32,32),dtype='float32');cx=.25+.04*w;cy=.5+.1*np.sin(np.deg2rad(angle));gauss=np.exp(-((xyz[0]-cx)**2+(xyz[1]-cy)**2+(xyz[2]-.4)**2)/.02);v[0]=gauss;v[1]=gauss*.5;v[5]=gauss*.2;targets.append(v)
x=torch.from_numpy(np.stack(conditions));y=torch.from_numpy(np.stack(targets));start=time.monotonic()
with torch.no_grad():initial=float(loss(model(x),y))
for step in range(201):
 ix=torch.tensor(rng.choice(4,2,replace=False));p=model(x[ix]);l=loss(p,y[ix]);opt.zero_grad();l.backward();opt.step()
with torch.no_grad():final=float(loss(model(x),y))
report=dict(roundtrip_passed=True,synthetic_initial_loss=initial,synthetic_final_loss=final,loss_ratio=final/initial,seconds=time.monotonic()-start,scope='Implementation sanity check on known Gaussian fields; not FDS accuracy or generalization evidence.')
(ROOT/'results/cnn-sanity.json').write_text(json.dumps(report,indent=2));print(report);assert final<initial*.2
