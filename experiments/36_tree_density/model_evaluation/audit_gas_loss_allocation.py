"""TRAIN observed-history residual/loss allocation proxy; not window-gradient evidence."""
from pathlib import Path
import ast,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02'
sys.path.insert(0,str(D));from model import Transition
torch.set_num_threads(4);a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());ids=torch.tensor(meta['rotations'][0]['train']);raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
names={'history_at','advance','predictions'};nodes=[n for n in ast.parse((D/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];ns=dict(torch=torch,external=external);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-inference','exec'),ns)
with torch.inference_mode():pred=ns['predictions'](model,z,ids,False)
truth=raw[ids,1:];phys=torch.sinh(pred*std+mean)*scale;errors=(pred-z[ids,1:]).square()/3;active=(truth[:,:,2]>1e-6)|((truth[:,:,:2]-raw[ids,:-1,:2]).abs().amax(-1)>1e-5);weights=torch.zeros_like(active,dtype=torch.float32)
for j,i in enumerate(ids.tolist()):
 ac=active[j];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas=int((config[ids]==config[i]).sum());weights[j]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas
counts=torch.zeros(90)
for j in range(59):counts[j:j+32]+=1
startup=times[ids,1:]<=32.2;peak=raw[ids,:,2].amax(1);strong=startup&(truth[:,:,2]>=.5*peak[:,None]);under=strong&(phys[:,:,2]<truth[:,:,2]);total=(errors*weights[:,:,None]*counts[None,:,None]).sum()
regions={}
for name,mask in [('startup32',startup),('strong_startup_gas',strong),('underpredicted_strong_startup_gas',under),('after32',~startup)]:
 allocated=errors*weights[:,:,None]*counts[None,:,None]*mask[:,:,None];regions[name]=dict(points=int(mask.sum()),all_state_loss_fraction=float(allocated.sum()/total),gas_loss_fraction_of_all_states=float(allocated[:,:,2].sum()/total),physical_gas_MAE_kg_s=float((phys[:,:,2]-truth[:,:,2]).abs()[mask].mean()),signed_gas_error_kg_s=float((phys[:,:,2]-truth[:,:,2])[mask].mean()))
out=dict(train_only=True,optimizer_updates=0,histories=len(ids),checkpoint_epoch=ck['epoch'],feature_loss_fractions=((errors*weights[:,:,None]*counts[None,:,None]).sum((0,1))/total).tolist(),normalization_std=std.tolist(),regions=regions,scope='Observed-history one-step state-loss proxy with exact per-history activity/replica weights and h32 window multiplicity. Full training windows use autonomous predictions after their origins; this proxy is NOT their actual loss or parameter gradient. Excludes supervised gate BCE. Strong means truth gas>=50% of each full-history gas peak and endpoint<=32.2s. Physical errors pooled over histories/points within each mask; loss coefficients include replica balancing. No validation/test or optimization.')
(R/'results/gas-loss-allocation-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
