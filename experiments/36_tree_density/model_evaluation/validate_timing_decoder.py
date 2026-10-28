"""Fit-only preservation, learnability and causality checks; no optimizer."""
from pathlib import Path
import hashlib,json
import torch
from context_decoder import JointDecoder as ContextDecoder
from timing_decoder import JointDecoder as TimingDecoder
from context_data import ContextData
R=Path(__file__).resolve().parents[1];D=R/'data/context-decoder-pilot01';O=R/'data/context-decoder-pilot01-results';torch.set_num_threads(4)
outpath=R/'results/timing-decoder-preflight.json';outpath.write_text(json.dumps(dict(passed=False,status='running'))+'\n');assert json.loads((R/'results/context-decoder-pilot01-analysis.json').read_text())['passed'];d=ContextData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);selected=torch.load(O/'physical_primary-selected.pt',map_location='cpu',weights_only=False);assert selected['epoch']==230 and selected['apply_decoder'];args=(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);base=ContextDecoder(*args);base.load_state_dict(selected['model']);torch.manual_seed(3640);m=TimingDecoder(*args);loaded=m.load_state_dict(selected['model'],strict=False);assert not loaded.unexpected_keys and set(loaded.missing_keys)=={'rw1','rb1','rw2','rb2','time_centres_s','time_widths_s'};before={k:v.clone() for k,v in m.state_dict().items()};ids=d.roles['fit'][:128];reports=[]
for origin,length in [(0,90),(0,16),(16,16),(74,16)]:
 x=d.x[ids] if length==90 else d.rx[ids,origin];b=d.base[ids] if length==90 else d.rb[ids,origin];state=d.raw[ids,origin];times=d.times[ids,origin:origin+length+1]
 with torch.inference_mode():
  expected=base(x,b,state,times);actual=m(x,b,state,times);assert torch.equal(expected,actual);assert (actual[:,:,:2]>=0).all() and (actual[:,:,2]>=0).all();curves=torch.cat([state[:,:2].clamp_min(0)[:,None],actual[:,:,:2]],1);assert ((curves[:,1:]-curves[:,:-1])<=1e-6).all()
 reports.append(dict(origin=origin,steps=length,old_guarded_prediction_bitwise_preserved=True))
# Actual fit-only derivatives for both ordinary physical and stronger startup terms.
from context_objective import objective
normalization=json.loads((D/'loss-normalization.json').read_text());small=ids[:16];origins=torch.tensor([-1,0,-1,16,-1,74,-1,8]*2);a=d.training_batch(m,small,origins);loss,parts=objective(*a[:4],d.scales,d.std,*a[4:],**d.objective_metadata(small,origins),normalization=normalization);loss.backward();assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in [m.rw1,m.rb1,m.rw2,m.rb2]);assert (m.rw2.grad.norm(dim=1)>0).all();assert all(p.grad is None for p in [m.w1,m.b1,m.w2,m.b2]);assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
# A random nonzero residual tests prefix invariance, not fitting.
with torch.no_grad():
 m.rw2.normal_(std=.01);m.rb2.normal_(std=.01);full=m(d.x[small],d.base[small],d.raw[small,0],d.times[small]);short=m(d.x[small,:16],d.base[small,:16],d.raw[small,0],d.times[small,:17]);assert torch.allclose(full[:,:16],short,rtol=1e-5,atol=2e-5)
result=dict(passed=True,optimizer_updates=0,fit_histories=128,confirmation_not_evaluated=True,test_not_evaluated=True,trainable_parameters=sum(p.numel() for p in m.parameters() if p.requires_grad),frozen_context_parameters=sum(p.numel() for p in m.parameters() if not p.requires_grad),checks=reports,all_four_residual_head_gradients_nonzero=True,frozen_context_gradients_absent=True,parameters_unchanged_during_derivative_check=True,nonzero_probe_prefix_invariant=True,source_sha256=hashlib.sha256((R/'model_evaluation/timing_decoder.py').read_bytes()).hexdigest(),scope='New residual is untrained; its zero initialization exactly reproduces guarded but unaccepted context01primary230, not rawGRU. Time bases use only known absolute/elapsed forecast seconds, not future target states or true phases. Fixed3s early widths are a model design, not extra simulator resolution. No optimizer, improved accuracy, capacity bound or physical validation.')
outpath.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
