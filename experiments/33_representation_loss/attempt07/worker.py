"""Cloud gradient diagnostic only: no optimizer steps, development data only."""
from worker_base import *
from previous_loss import quantities
from torch.nn import functional as F

def terms(p,y,ambient):
 t,q,g=quantities(p);ty,qy,gy=quantities(y);dims=(1,2,3)
 def region(v,m):
  n=m.sum(dims);return ((v*m).sum(dims)/n.clamp_min(1))[n>0].mean() if (n>0).any() else v.sum()*0
 hot=ty>50;bright=gy>5
 total=q.sum(dims)*.125;truth=qy.sum(dims)*.125
 alloc=q/q.sum(dims,keepdim=True).clamp_min(1e-12);target=qy/qy.sum(dims,keepdim=True).clamp_min(1e-12);active=truth>1
 kl=(target*(target.clamp_min(1e-12).log()-alloc.clamp_min(1e-12).log())).sum(dims)
 excess=(g-ambient).clamp_min(0);ref=(gy-ambient).clamp_min(0)
 return dict(temperature_hot=region((p[:,0]-y[:,0]).square(),hot),temperature_background=.1*region((p[:,0]-y[:,0]).square(),~hot),strength=.5*F.smooth_l1_loss(torch.log1p(total),torch.log1p(truth)),allocation=.1*(kl[active].mean() if active.any() else p.sum()*0),radiation_bright=region((p[:,5]-y[:,5]).square(),bright),radiation_background=.1*region((p[:,5]-y[:,5]).square(),~bright),candidate_radiation_excess=(excess.sum(0)-ref.sum(0)).abs().mean()/(ref.sum(0).mean()+1),candidate_temperature_physical=(t-ty).abs().mean()/(abs(ty-20).mean()+1))

def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);cs=json.loads((R/'cases.json').read_text());train=[c for c in cs if c['split']=='train'];geoms=dict(np.load(R/'data/geometries.npz'));rows=[]
 # Fixed six training configurations; no validation or test gradients.
 selected=train[::2]
 for arm in ['current','loss_only','spatial_heads']:
  m=(SpatialHeads() if arm=='spatial_heads' else GeometryCNN()).cuda();saved=torch.load(R/'data/resume'/f'{arm}.pt',map_location='cuda',weights_only=False);m.load_state_dict(saved['model']);m.eval()
  named=[(n,p) for n,p in m.named_parameters() if n.startswith(('e0.','e1.','e2.'))] if arm=='spatial_heads' else [(n,p) for n,p in m.named_parameters() if n.startswith('fc.')]
  params=[p for n,p in named]
  for c in selected:
   a,t=load(c);ambient=torch.tensor(np.array(a[0,5]),device='cuda')
   for center in [10.,30.,120.]:
    k=int(abs(t-center).argmin());p=predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda');y=torch.tensor(encode(a[k:k+3],c['wind_speed']),device='cuda');ts=terms(p,y,ambient);grads={}
    for n,l in ts.items():
     gg=torch.autograd.grad(l,params,retain_graph=True,allow_unused=True);grads[n]=torch.cat([(torch.zeros_like(pp) if z is None else z).reshape(-1) for z,pp in zip(gg,params)])
    cos={}
    for n,g in grads.items():
     for nn,gg in grads.items():
      if n<nn:cos[n+' / '+nn]=float(F.cosine_similarity(g,gg,dim=0)) if g.norm()>0 and gg.norm()>0 else None
    rows.append(dict(arm=arm,case=c['case'],time_s=t[k:k+3].tolist(),checkpoint_step=saved['step'],losses={n:float(l.detach()) for n,l in ts.items()},gradient_norms={n:float(g.norm()) for n,g in grads.items()},gradient_cosines=cos,parameter_scope=[n for n,p in named]))
  del m;torch.cuda.empty_cache()
 raw=json.dumps(dict(scope='No optimizer updates. Six training configurations, three windows each. Gradient conflict/scales are local diagnostics, not proof of causal training failure. Candidate losses are not trained.',rows=rows),indent=2).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();upload('error.txt',msg.encode());raise
