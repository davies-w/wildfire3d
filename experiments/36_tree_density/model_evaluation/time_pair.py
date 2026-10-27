"""Cloud-only matched pair preflight: full stride-one epoch backward timings, no fitting."""
from pathlib import Path
import json,time,io
R=Path(__file__).resolve().parent
source=(R/'worker.py').read_text().split('reports=[]')[0]
assert 'optimizer=' not in source
ns={'__file__':str(R/'worker.py')};exec(compile(source,'pair-preflight','exec'),ns)
globals().update({k:v for k,v in ns.items() if not k.startswith('__')})
train=torch.tensor(meta['rotations'][0]['train'],device=device);valid=torch.tensor(meta['rotations'][0]['validation'],device=device)
mean,std=normalize_fit(raw,train,config,scale);z=(torch.asinh(raw/scale)-mean)/std
weights=torch.zeros(2080,90,device=device)
for n in train.tolist():
 ac=active[n];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas=int((config[train]==config[n]).sum());weights[n]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas
rows=[]
for kind in P['arms']:
 torch.manual_seed(3516);model=Transition(kind).to(device);model.set_normalization(mean,std)
 with torch.no_grad():model.head.weight.fill_(.001)
 for h in (1,8,16,32):
  windows=[(n,j) for n in train.tolist() for j in range(91-h)];order=np.random.default_rng(3516).permutation(len(windows));model.train();torch.cuda.synchronize();begin=time.monotonic();batches=0
  for off in range(0,len(windows),P['batch_windows']):
   batch=[windows[i] for i in order[off:off+P['batch_windows']]];ids=torch.tensor([n for n,j in batch],device=device);js=torch.tensor([j for n,j in batch],device=device);hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js);loss=0.;normal=0.
   for step in range(h):
    jj=js+step;state,memory=model.step(hist,external[ids,jj],memory);state_loss=training_objective(state,z[ids,jj+1])
    if kind=='gated':
     supervised=gate_supervised[ids,jj];bce=F.binary_cross_entropy_with_logits(model.last_gate_logits,gate_targets[ids,jj],reduction='none');state_loss+=P['gate_loss_weight']*(bce*supervised).sum(-1)/supervised.sum(-1).clamp_min(1)
    loss+=(state_loss*weights[ids,jj]).sum();normal+=len(ids);hist=advance(hist,state)
   loss=loss/normal;assert bool(torch.isfinite(loss));model.zero_grad(set_to_none=True);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters());batches+=1
  torch.cuda.synchronize();rows.append(dict(kind=kind,horizon=h,windows=len(windows),batches=batches,seconds=time.monotonic()-begin))
 torch.cuda.synchronize();begin=time.monotonic()
 for ids in (train,valid):
  result=evaluate(model,z,ids,mean,std);assert all(result[m]['finite'] for m in ('one_step','rollout'))
 torch.cuda.synchronize();rows.append(dict(kind=kind,evaluation_seconds=time.monotonic()-begin))
save('timing.json',dict(passed=True,training=False,optimizer_created=False,test_evaluated=False,measurements=rows,margin_policy='Measure complete full-window epochs; later projection adds optimizer/checkpoint overhead and compute margin.'))
save('complete.json',dict(passed=True,training=False))
