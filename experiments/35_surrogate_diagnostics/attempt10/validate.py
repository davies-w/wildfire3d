"""Meaningful preflight: gradients, metrics, disjointness, bounds and serialization; no fitting."""
from pathlib import Path
import ast,io,json,hashlib
import numpy as np,torch
from model import FieldUNet,encode,physical,channel_losses
from metrics import statistics,summarize_case,aggregate
R=Path(__file__).parent;torch.set_num_threads(4)
for p in R.glob('*.py'):ast.parse(p.read_text())
plan=json.loads((R/'coverage-plan.json').read_text());cases=json.loads((R/'cases.json').read_text());train=[c for c in cases if c['split']=='train'];val=[c for c in cases if c['split']=='validation'];assert len(train)==8 and len(val)==40 and len({c['configuration'] for c in val})==32
assert not ({c['configuration'] for c in train}&{c['configuration'] for c in val});assert all(c['split'] in ['train','validation'] for c in cases)
scales=torch.tensor(json.loads((R/'scales.json').read_text())['encoded_std']);assert (scales>=.04999).all()
for c in cases:
 a=np.load(R/'data/fields'/(c['case']+'.npy'),mmap_mode='r');t=np.load(R/'data/fields'/(c['case']+'-time.npy'));assert a.shape==(91,6,48,32,32) and len(t)==91 and np.all(np.diff(t)>0)
# Wrong negative encoded HRR must receive a nonzero derivative, unlike the removed clamp.
y=torch.zeros((1,6,8,8,8));y[:,1,0,0,0]=1;p=torch.full_like(y,-.1,requires_grad=True);loss=channel_losses(p,y,torch.ones(6))[0].mean();loss.backward();assert p.grad[:,1,0,0,0].abs().item()>0
# For exactly one positive and constant error inside each region, each region receives half.
z=torch.zeros_like(y);z[:,1]=1;z[:,1,0,0,0]=3;terms,_=channel_losses(z,y,torch.ones(6));assert abs(terms[0,1].item()-2.5)<1e-6
cold=torch.zeros_like(y);terms,whole=channel_losses(z,cold,torch.ones(6));assert torch.equal(terms,whole)
# Physical metrics on identity predictions must be essentially zero, not an indexing artifact.
a=torch.zeros((3,6,8,8,8));a[:,0]=20;a[:,0,1,1,1]=120;a[:,1,1,1,1]=20;a[:,2]=2;a[:,5]=.2;e=encode(a,2);v=statistics(e,e,a,2,torch.ones(6));summary=summarize_case(v,np.array([0,30,180.]))
assert summary['all']['objective_MSE']==0 and summary['all']['total_HRR_relative_L1_percent']<1e-4 and summary['all']['hot_f1']==1
# Whole 0.5m grid shape and exact CPU inference serialization replay.
torch.manual_seed(plan['seed']);m=FieldUNet().eval();x=torch.zeros((1,14,48,32,32))
with torch.no_grad():out=m(x);assert out.shape==(1,6,48,32,32) and torch.isfinite(out).all()
b=io.BytesIO();torch.save(m.state_dict(),b);b.seek(0);m.load_state_dict(torch.load(b,weights_only=True))
with torch.no_grad():assert torch.equal(out,m(x))
# Independent arms can initialize identically without sharing parameter storage.
torch.manual_seed(plan['seed']);other=FieldUNet();assert all(torch.equal(a,b) and a.data_ptr()!=b.data_ptr() for a,b in zip(m.parameters(),other.parameters()))
proof=dict(passed=True,parameters=sum(p.numel() for p in m.parameters()),cases=len(cases),gradient_nonzero_for_negative_HRR=True,region_balance_arithmetic=True,identity_metrics=True,CPU_forward_restore_exact=True,independent_initialization_exact=True,scope='CPU synthetic inference and derivative checks only; no optimizer/local fitting. Actual CUDA check required before training.')
(R/'results/preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
