"""Fit-only local gradient directions at preserved checkpoints; no optimizer or test evaluation."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/canonical-pilot03';O=R/'data/canonical-pilot03-results';sys.path.insert(0,str(D))
from canonical_data import CanonicalData
from joint_decoder import JointDecoder
from guard_matched_objective import objective
load=lambda p:json.loads(p.read_text())
assert load(R/'results/canonical-pilot03-analysis.json')['passed']
torch.set_num_threads(4);torch.manual_seed(3640);d=CanonicalData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);normalization=load(D/'loss-normalization.json');rng=np.random.default_rng(364003);fit=d.roles['fit'];draws=[]
for batch in range(3):
 ids=fit[torch.tensor(rng.choice(len(fit),64,replace=False))];origins=torch.tensor(rng.integers(0,75,64));origins[::2]=-1;canonical={h:torch.tensor(rng.integers(0,91-h,64)) for h in [1,4,8,16,45]};draws.append((ids,origins,canonical))
reports=[]
for epoch in [0,60,550]:
 ck=initial if epoch==0 else torch.load(O/f'canonical_half-epoch{epoch:03}.pt',map_location='cpu',weights_only=False)
 m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);m.load_state_dict(ck['model']);m.eval();before={k:v.clone() for k,v in m.state_dict().items()};params=[p for p in m.parameters() if p.requires_grad]
 def gradient(loss):
  g=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True);v=torch.cat([(torch.zeros_like(p) if q is None else q).reshape(-1) for p,q in zip(params,g)]);assert torch.isfinite(v).all();return v
 def cosine(a,b):
  den=a.norm()*b.norm();return float(torch.dot(a,b)/den) if den>0 else None
 for batch,(ids,origins,co) in enumerate(draws):
  args=d.training_batch(m,ids,origins);_,parts=objective(*args[:4],d.scales,d.std,*args[4:],**d.objective_metadata(ids,origins),normalization=normalization)
  weights=dict(physical=1.,encoded_nonharm=.25,quiet_nonharm=1.,under_tail=.3,over_tail=.15,peak_error=.05,sampling_residual_error=.1)
  losses={k:parts[k]*w for k,w in weights.items()};canonical={}
  for h in [1,4,8,16,45]:
   b=d.canonical_batch(m,ids,torch.full_like(ids,h),co[h]);error=(b['prediction']-b['truth']).abs()/b['normalizers'];per_state=d.canonical_case_factor*(error*b['replica_weight'][:,None]).mean(0)/4
   for state in range(4):losses[f'canonical_h{h}_state{state}']=.1*per_state[state]
  gradients={name:gradient(loss) for name,loss in losses.items()};total=sum(gradients.values());heat=gradients['canonical_h1_state3'];under=gradients['under_tail']
  record=dict(epoch=epoch,batch=batch,fit_source_ids=d.source_ids[ids.numpy()].tolist(),losses={k:float(v.detach()) for k,v in losses.items()},gradient_norms={k:float(v.norm()) for k,v in gradients.items()},total_gradient_norm=float(total.norm()),global_clip1_scale=min(1.,1/max(float(total.norm()),1e-30)),startup_under_cosine={k:cosine(under,v) for k,v in gradients.items()},h1_heating_cosine={k:cosine(heat,v) for k,v in gradients.items()},h1_heating_cosine_with_total=cosine(heat,total),startup_under_cosine_with_total=cosine(under,total))
  assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items());assert not d.confirmation_open;reports.append(record);print('fit gradient audit',epoch,batch,'clip',record['global_clip1_scale'],'short heat vs total',record['h1_heating_cosine_with_total'],'startup vs total',record['startup_under_cosine_with_total'],flush=True)
assert len(reports)==9
out=dict(passed=True,optimizer_updates=0,parameters_unchanged=True,fit_only=True,test_evaluated=False,confirmation_evaluated=False,arm='canonical_half',snapshots=[0,60,550],reports=reports,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Three fixed64history fit batches per snapshot. Same cases/draws across checkpoints. Sum original balanced regime terms plus coefficient0.5 times the average of separately sampled real canonical horizons; this approximates expected horizon sampling, not a serialized training update. Cosines compare loss gradients, not actual AdamW-preconditioned updates. Negative cosine indicates local first-order conflict, not population causality or proof of an unavoidable accuracy floor. Global clip1 scale is descriptive; no optimizer, parameter update, new checkpoint selection or threshold change.')
(R/'results/canonical-pilot03-fit-gradient-audit.json').write_text(json.dumps(out,indent=2)+'\n')
