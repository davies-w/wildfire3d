"""Fit residuals and local objective-gradient conflicts; never update parameters."""
from pathlib import Path
import hashlib,json,sys
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/context-decoder-pilot01';O=R/'data/context-decoder-pilot01-results';sys.path.insert(0,str(D))
from context_data import ContextData
from joint_decoder import JointDecoder
from context_objective import objective
load=lambda p:json.loads(p.read_text());assert load(R/'results/context-decoder-pilot01-analysis.json')['passed'];torch.set_num_threads(4);d=ContextData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);snapshot=torch.load(O/'physical_primary-selected.pt',map_location='cpu',weights_only=False);assert snapshot['apply_decoder'];m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']);m.load_state_dict(snapshot['model']);before={k:v.clone() for k,v in m.state_dict().items()};normalization=load(D/'loss-normalization.json')
with torch.inference_mode():baseline=d.score(None,d.roles['fit']);fit=d.score(m,d.roles['fit'])
ratios={rg:[y/x for x,y in zip(baseline[rg]['physical_MAE_by_feature'],fit[rg]['physical_MAE_by_feature'])] for rg in ['autonomous','display']};reports=[]
for seed in [3630,3631,3632]:
 generator=torch.Generator().manual_seed(seed);ids=d.roles['fit'][torch.randperm(len(d.roles['fit']),generator=generator)[:128]];origins=torch.where(torch.arange(128)%2==0,torch.full((128,),-1),torch.randint(0,75,(128,),generator=generator));args=d.training_batch(m,ids,origins);loss,parts=objective(*args[:4],d.scales,d.std,*args[4:],**d.objective_metadata(ids,origins),normalization=normalization);vectors={}
 for name,term in parts.items():
  gradients=torch.autograd.grad(term,tuple(m.parameters()),retain_graph=True,allow_unused=True);vectors[name]={head:torch.cat([(torch.zeros_like(p) if g is None else g)[head].flatten() for p,g in zip(m.parameters(),gradients)]) for head in [2,3]}
 def cosine(a,b):
  denominator=a.norm()*b.norm();return float(torch.dot(a,b)/denominator) if denominator>0 else None
 reports.append(dict(seed=seed,histories=128,physical_gas_vs_under_tail_cosine=cosine(vectors['physical'][2],vectors['under_tail'][2]),gas_gradient_norm_by_component={n:float(v[2].norm()) for n,v in vectors.items()},heating_gradient_norm_by_component={n:float(v[3].norm()) for n,v in vectors.items()},loss=float(loss.detach())))
assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
out=dict(passed=True,optimizer_updates=0,parameters_unchanged=True,epoch=snapshot['epoch'],fit_histories=len(d.roles['fit']),fit_MAE_ratios=ratios,fit_baseline=baseline,fit_candidate=fit,gradient_audits=reports,selection_and_confirmation_not_used_for_derivatives=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Posthoc fit-only mechanism audit of the frozen guarded but unaccepted physical-primary checkpoint. Gradient norms are unweighted components, not Adam step sizes; negative cosine shows local competing directions in these batches, not proof of finite-update behavior, a unique cause or a capacity/error bound. No new model chosen or deployed.')
(R/'results/context-fit-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['fit_baseline','fit_candidate']},indent=2))
