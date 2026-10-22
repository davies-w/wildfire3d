"""Direct initial-condition predictors; no physical time stepping at inference."""
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn
ROOT=Path(__file__).resolve().parent
FACES=['west','east','south','north','roof']
CENTERS=np.array([[14,12,2],[20,12,2],[17,10,2],[17,14,2],[17,12,4]],dtype=float)
NORMALS=np.array([[-1,0,0],[1,0,0],[0,-1,0],[0,1,0],[0,0,1]],dtype=float)
TIMES=np.array([15,30,45,60,75,90],dtype=float)

def features(layout,power,duration=30):
    anchors=json.loads((ROOT/'design.json').read_text())['anchors_m']
    crowns=np.array([[*anchors[a],1.13] for a in layout],dtype=float);n=len(crowns)
    # Five fixed surface patches, followed by up to three variable fuel regions.
    pos=np.zeros((8,3));pos[:5]=CENTERS;pos[5:5+n]=crowns
    mask=np.zeros(8);mask[:5+n]=1
    x=np.zeros((8,12));x[:,:3]=(pos-[14,12,0])/10
    x[5:5+n,3]=1; x[5:5+n,4]=power/n/1600
    x[5:5+n,5]=1; x[5:5+n,6]=.14
    x[:5,7:10]=NORMALS;x[:5,10]=.02;x[5:5+n,10]=1.96/10
    x[5:5+n,11]=duration/30
    x*=mask[:,None]
    # edge[i,j] describes sender j relative to receiver i.
    delta=pos[None,:,:]-pos[:,None,:];distance=np.linalg.norm(delta,axis=-1)
    safe=np.maximum(distance,.1);normals=np.zeros((8,3));normals[:5]=NORMALS
    facing=np.sum(normals[:,None,:]*delta,axis=-1)/safe
    edge=np.concatenate([delta/10,distance[:,:,None]/10,
        (1/(1+distance**2))[:,:,None],(delta[:,:,0]/safe)[:,:,None],
        facing[:,:,None],np.abs(delta[:,:,2:3])/safe[:,:,None]],axis=-1)
    # All-to-all physical context, except self and padded slots.
    adjacency=mask[:,None]*mask[None,:]*(1-np.eye(8))
    gaps=np.maximum(14-crowns[:,0]-.85,.1)
    lateral=np.maximum(np.abs(crowns[:,1]-12)-2,0)
    d2=gaps**2+lateral**2
    simple=np.array([power/1600,n/3,gaps.min()/10,
        np.sum(1/(1+d2)),np.sum((power/n/1600)/(1+d2)),
        np.sum(np.exp(-lateral**2)/(1+gaps**2)),crowns[:,0].mean()/24,
        np.std(crowns[:,1])/10,1.,duration/30])
    return tuple(torch.tensor(a,dtype=torch.float32) for a in (x,edge,adjacency,simple))

def batch(cases):
    return tuple(torch.stack(parts) for parts in zip(*(features(r['layout'],r['total_source_kw'],r.get('duration_s',30)) for r in cases)))

class Graph(nn.Module):
    def __init__(self,interaction=True):
        super().__init__(); self.interaction=interaction
        self.encode=nn.Sequential(nn.Linear(12,8),nn.Tanh())
        self.messages=nn.ModuleList([nn.Sequential(nn.Linear(24,8),nn.Tanh(),nn.Linear(8,8)) for _ in range(2)])
        self.updates=nn.ModuleList([nn.Sequential(nn.Linear(16,8),nn.Tanh()) for _ in range(2)])
        self.aux=nn.Linear(8,12)
        self.output=nn.Sequential(nn.Linear(16,8),nn.Tanh(),nn.Linear(8,2))
    def forward(self,x,edge,adjacency,simple):
        h=self.encode(x);a=adjacency.clone()
        if not self.interaction:
            # Independent crown encodings; only their additive messages reach faces.
            a[:,5:,:]=0;a[:,:5,:5]=0
        active=(x.abs().sum(-1)>0).float()
        for message,update in zip(self.messages,self.updates):
            receiver=h[:,:,None,:].expand(-1,-1,8,-1)
            sender=h[:,None,:,:].expand(-1,8,-1,-1)
            m=message(torch.cat([receiver,sender,edge],-1))*a[:,:,:,None]
            changed=update(torch.cat([h,m.sum(2)/4],-1))
            if not self.interaction:
                h=torch.cat([changed[:,:5],h[:,5:]],1)
            else:h=changed
            h=h*active[:,:,None]
        pooled=torch.cat([h[:,:5].mean(1),h[:,:5].amax(1)],-1)
        return self.output(pooled),self.aux(h[:,:5])

class Simple(nn.Module):
    def __init__(self):
        super().__init__();self.output=nn.Linear(10,2);self.aux=nn.Linear(10,60)
    def forward(self,x,edge,adjacency,simple):
        return self.output(simple),self.aux(simple).reshape(-1,5,12)

class IgnitionOnly(nn.Module):
    """Ten-parameter logistic baseline; the constant input supplies the intercept."""
    def __init__(self):
        super().__init__();self.output=nn.Linear(10,1,bias=False)
    def forward(self,x,edge,adjacency,simple):
        return self.output(simple),None

def model(kind):
    if kind=='ignition_only':return IgnitionOnly()
    return Simple() if kind=='simple' else Graph(kind=='graph')

def loss(outputs,target,auxiliary):
    heads,aux=outputs
    classification=nn.functional.binary_cross_entropy_with_logits(heads[:,0],target[:,0])
    if aux is None:return classification
    # Negative cases are right-censored: only penalize a predicted time below the horizon.
    predicted=torch.nn.functional.softplus(heads[:,1])
    time_error=torch.where(target[:,0]>0,(predicted-target[:,1]).square(),torch.relu(1-predicted).square()).mean()
    return classification+.1*nn.functional.smooth_l1_loss(aux,auxiliary)+.05*time_error

def smoke():
    torch.set_num_threads(1);torch.manual_seed(0)
    cases=[dict(layout=l,total_source_kw=800) for l in ('A','AB','ABC')]
    f=batch(cases);target=torch.tensor([[0.,1.],[1.,.4],[1.,.3]])
    counts={}
    for kind in ('graph','additive','simple','ignition_only'):
        m=model(kind);outputs=m(*f);v=loss(outputs,target,torch.zeros(3,5,12));v.backward()
        assert torch.isfinite(v) and all(torch.isfinite(p.grad).all() for p in m.parameters() if p.grad is not None)
        # The graph must be invariant to permutations of the fuel nodes.
        perm=torch.tensor([0,1,2,3,4,7,5,6])
        changed=m(f[0][:,perm],f[1][:,perm][:,:,perm],f[2][:,perm][:,:,perm],f[3])
        assert torch.allclose(outputs[0],changed[0],atol=1e-6)
        counts[kind]=sum(p.numel() for p in m.parameters())
    (ROOT/'results/model-smoke.json').write_text(json.dumps(dict(passed=True,parameters=counts,
        differentiable=True,fuel_permutation_invariant=True),indent=2)+'\n')
    print('Synthetic model checks passed:',counts)
if __name__=='__main__':smoke()
