"""Check algebraically equivalent configuration means; no optimizer or test data evaluation."""
from pathlib import Path
import hashlib,json,sys,time
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/model-preflight';sys.path.insert(0,str(D))
old="def mean_groups(value,ids):return torch.stack([value[config[ids]==c].mean(0) for c in torch.unique(config[ids])]).mean(0)"
new="""def mean_groups(value,ids):
 # Equal configuration weight: each history contributes inverse replica count.
 _,inverse,counts=torch.unique(config[ids],return_inverse=True,return_counts=True)
 weights=counts[inverse].to(value.dtype).reciprocal()
 return (value*weights.reshape((-1,)+(1,)*(value.ndim-1))).sum(0)/len(counts)"""
def main():
 source=(R/'data/model-runner/worker.py').read_text();assert source.count(old)==1
 candidate=source.replace(old,new);assert candidate.replace(new,old)==source
 torch.set_num_threads(4);torch.manual_seed(3516)
 ns=[]
 for text in (source,candidate):
  prefix=text.split('checks=[]')[0].replace("assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'",'').replace("device='cuda'","device='cpu'")
  assert 'optimizer=' not in prefix
  scope={'__file__':str(D/'worker.py')};exec(compile(prefix,'report-check','exec'),scope);ns.append(scope)
 # Randomized unequal replica counts and multidimensional values check group weighting.
 rng=np.random.default_rng(20261027)
 for _ in range(30):
  ids=torch.tensor(rng.choice(2080,size=200,replace=False));values=torch.tensor(rng.normal(size=(200,7,4)),dtype=torch.float32)
  assert torch.allclose(ns[0]['mean_groups'](values,ids),ns[1]['mean_groups'](values,ids),rtol=1e-5,atol=1e-7)
 train=torch.tensor(ns[0]['meta']['rotations'][0]['train']);mean,std=ns[0]['normalize_fit'](ns[0]['raw'],train,ns[0]['config'],ns[0]['scale']);z=(torch.asinh(ns[0]['raw']/ns[0]['scale'])-mean)/std
 model=ns[0]['Transition']();model.set_normalization(mean,std)
 with torch.no_grad():model.head.weight.fill_(.001)
 results=[];seconds=[]
 for scope in ns:
  started=time.monotonic();results.append(scope['evaluate'](model,z,train,mean,std,True));seconds.append(time.monotonic()-started)
 errors=[]
 def compare(a,b):
  if isinstance(a,dict):
   assert a.keys()==b.keys()
   for k in a:compare(a[k],b[k])
  elif isinstance(a,list):
   assert len(a)==len(b)
   for x,y in zip(a,b):compare(x,y)
  elif isinstance(a,float):
   assert np.isclose(a,b,rtol=1e-5,atol=1e-7),(a,b)
   errors.append(abs(a-b))
  else:assert a==b
 compare(*results)
 dest=R/'data/model-report-candidate';dest.mkdir(exist_ok=True);(dest/'worker.py').write_text(candidate)
 report={'passed':True,'training':False,'test_evaluation':False,'only_mean_groups_changed':True,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'random_weighting_checks':30,'train_histories_checked':len(train),'max_absolute_metric_difference':max(errors),'tolerance':{'rtol':1e-5,'atol':1e-7},'cpu_seconds_original_candidate':seconds,'limitation':'Same equal-configuration metric equation, different floating-point reduction order. Not bitwise identical; GPU deterministic equivalence and timing still required before adoption. No optimizer, training loss, or architecture changes.'}
 (R/'results/model-fast-reporting-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
