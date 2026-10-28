"""CPU derivative/arithmetic audit of the proposed deterministic CUDA replacement.

No optimizer. CUDA next-update replay is still required in a separately bounded
future trial; CPU arithmetic cannot prove GPU kernel availability.
"""
from pathlib import Path
import hashlib,json
import torch
from joint_decoder_v2 import deterministic_prefix_sum
R=Path(__file__).resolve().parents[1];torch.set_num_threads(4);torch.manual_seed(3620);reports=[]
for shape,dim in [((128,),0),((128,90),1),((128,90,2),1),((128,16,2),1)]:
 x=torch.randn(shape,requires_grad=True);probe=torch.randn(shape);a=deterministic_prefix_sum(x,dim);b=x.cumsum(dim);ga=torch.autograd.grad((a*probe).sum(),x,retain_graph=True)[0];gb=torch.autograd.grad((b*probe).sum(),x)[0];assert torch.allclose(a,b,atol=2e-5,rtol=2e-5) and torch.allclose(ga,gb,atol=2e-5,rtol=2e-5)
 reports.append(dict(shape=list(shape),dim=dim,max_value_error=float((a-b).abs().max().detach()),max_gradient_error=float((ga-gb).abs().max())))
proof=dict(passed=True,optimizer_updates=0,cpu_prefix_values_and_derivatives_match=True,cases=reports,source_hashes={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['joint_decoder_v2.py','joint_objective_v2.py']},cuda_tested=False,scope='Fix proposal for joint01 deterministic floating cumsum startup failure. CPU equivalence is not proof of CUDA execution, complete training, accuracy or acceptance. Original joint01 archive/source remains preserved.')
(R/'results/joint-prefix-sum-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
