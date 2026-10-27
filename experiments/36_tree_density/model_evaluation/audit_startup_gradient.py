"""Isolated frozen-checkpoint TRAIN gradients; no optimizer instantiated or updated."""
from pathlib import Path
import ast,json,sys
import numpy as np
import torch
import torch.nn.functional as F
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02';sys.path.insert(0,str(D));from model import Transition
torch.set_num_threads(4);a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());train=torch.tensor(meta['rotations'][0]['train']);raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;model=Transition('gated');model.load_state_dict(ck['model']);model.eval();active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5);weights=torch.zeros(len(raw),90)
for i in train.tolist():
 ac=active[i];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas=int((config[train]==config[i]).sum());weights[i]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas
names={'history_at','advance','prefix_memory'};nodes=[n for n in ast.parse((D/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];ns=dict(torch=torch,external=external);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-functions','exec'),ns)
rng=np.random.default_rng(20261027);ids=train[torch.tensor(rng.choice(len(train),256,replace=False))];origins=torch.tensor(rng.integers(0,59,len(ids)));params=list(model.parameters());plan=json.loads((D/'coverage-plan.json').read_text())
def vector(loss):
 g=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True)
 v=torch.cat([(torch.zeros_like(p) if v is None else v).flatten() for p,v in zip(params,g)]).detach();assert torch.isfinite(v).all();return v
def run(js):
 hist=ns['history_at'](z,ids,js);memory=ns['prefix_memory'](model,z,ids,js);state_losses=[];gate_losses=[];gas_losses=[];symmetric_losses=[];gas_parts={k:[] for k in ["over_startup","under_startup","after32"]}
 for step in range(32):
  jj=js+step;pred,memory=model.step(hist,external[ids,jj],memory);state_losses.append((pred-z[ids,jj+1]).square()*weights[ids,jj,None]/3)
  mask=torch.tensor(a['gate_supervised'])[ids,jj];target=torch.tensor(a['gate_targets'])[ids,jj];gate_losses.append(plan['gate_loss_weight']*(F.binary_cross_entropy_with_logits(model.last_gate_logits,target,reduction='none')*mask).sum(-1)/mask.sum(-1).clamp_min(1)*weights[ids,jj])
  phys=torch.sinh(pred[:,2]*std[2]+mean[2])*scale[2];truth=raw[ids,jj+1,2];peak=raw[ids,:,2].amax(1).clamp_min(.01);startup=(times[ids,jj+1]<=32.2);gas_losses.append(((truth-phys).clamp_min(0)/peak).square()*startup);symmetric_losses.append(((truth-phys)/peak).square()*startup)
  gas_encoded=(pred[:,2]-z[ids,jj+1,2]).square()*weights[ids,jj]/3
  for key,mask_part in [('over_startup',startup&(phys>truth)),('under_startup',startup&(phys<=truth)),('after32',~startup)]:gas_parts[key].append(gas_encoded*mask_part)
  hist=ns['advance'](hist,pred)
 features=torch.stack(state_losses).mean((0,1));gate=torch.stack(gate_losses).mean();original=features.sum()+gate;under=torch.stack(gas_losses).mean();vectors={k:vector(v) for k,v in [('original',original),('gas_state',features[2]),('other_states',features[[0,1,3]].sum()),('gate_BCE',gate),('startup_underprediction',under)]}
 part_losses={k:torch.stack(v).mean() for k,v in gas_parts.items()};part_losses['symmetric_relative_startup_gas']=torch.stack(symmetric_losses).mean();vectors.update({k:vector(v) for k,v in part_losses.items()})
 report=dict(gas_encoded_parts={k:float(v.detach()) for k,v in part_losses.items()},weighted_state_loss_by_feature=features.detach().tolist(),weighted_gate_BCE=float(gate.detach()),startup_underprediction_surrogate=float(under.detach()),gradient_norms={k:float(v.norm()) for k,v in vectors.items()})
 report['cosines_with_startup_underprediction']={k:float(torch.dot(v,vectors['startup_underprediction'])/(v.norm()*vectors['startup_underprediction'].norm()).clamp_min(1e-30)) for k,v in vectors.items()}
 return report,vectors['original']
replicates=[]
for seed in [20261027,20261028,20261029]:
 rng=np.random.default_rng(seed);ids=train[torch.tensor(rng.choice(len(train),256,replace=False))];origins=torch.tensor(rng.integers(0,59,len(ids)))
 random_report,random_gradient=run(origins);startup_report,startup_gradient=run(torch.zeros_like(origins));cos=float(torch.dot(random_gradient,startup_gradient)/(random_gradient.norm()*startup_gradient.norm()));replicates.append(dict(seed=seed,random_origins=random_report,startup_origins=startup_report,cosine_random_vs_startup_original_gradient=cos))
assert all(torch.equal(value,ck['model'][name]) for name,value in model.state_dict().items())
assert not set(train.tolist()) & (set(meta['rotations'][0]['validation'])|set(meta['rotations'][0]['test']))
out=dict(checkpoint_state_unchanged=True,all_gradients_finite=True,train_only=True,optimizer_instantiated=False,optimizer_updates=0,batch_histories=len(ids),seeds=[20261027,20261028,20261029],checkpoint_epoch=ck['epoch'],horizon_steps=32,replicates=replicates,scope='Three deterministic samples of256training histories (may overlap), random h32 origins versus origin0 on the same histories. Exact existing state+supervised gate BCE objectives and prefix-memory logic; startup surrogate is positive gas deficit squared normalized by each true full-history gas peak (floor0.01kg/s), endpoint<=32.2s. Symmetric relative gas loss is an exploratory alternative measuring both under- and overprediction in physical peak units; no candidate is selected or trained here. Gradients are local parameter derivatives at frozen epoch183, not optimizer steps or evidence of finite-update improvement. No validation/test, optimizer creation, or fitting. No population confidence interval; overlapping batches/parameter norms do not establish a unique cause.')
(R/'results/startup-gradient-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
