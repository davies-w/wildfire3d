"""CPU data isolation and synthetic model checks. No optimizer or held-out evaluation."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
import torch
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/dataset-completeness.json').read_text())['passed']
 a=np.load(R/'data/learning/sequences.npz');m=json.loads((R/'learning-schema.json').read_text());folds=json.loads((R/'data/grouped-folds.json').read_text())
 assert m['rotations']==folds['rotations'] and a['state'].shape==(2080,91,4)
 assert np.isfinite(a['state']).all() and np.isfinite(a['time']).all() and np.all(np.diff(a['time'],axis=1)>0)
 torch.set_num_threads(4);torch.manual_seed(3516)
 spec=importlib.util.spec_from_file_location('density_model',R/'data/model-runner/model.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 raw=torch.tensor(a['state']);config=torch.tensor(a['configuration']);scale=torch.tensor(m['physical_encoding_scales']);checks=[];tested=[]
 for rot in m['rotations']:
  train,valid,test=[np.array(rot[k]) for k in ('train','validation','test')]
  sets=[set(a['configuration'][ids]) for ids in (train,valid,test)]
  assert sum(map(len,(train,valid,test)))==2080 and len(set(np.concatenate([train,valid,test])))==2080
  assert all(not sets[i]&sets[j] for i in range(3) for j in range(i))
  assert len(sets[0])==1632 and len(sets[1])==len(sets[2])==204
  ids=torch.tensor(train);mean,std=mod.normalize_fit(raw,ids,config,scale)
  changed=raw.clone();changed[np.concatenate([valid,test])]=123456
  mean2,std2=mod.normalize_fit(changed,ids,config,scale)
  assert torch.equal(mean,mean2) and torch.equal(std,std2),'Held-out leakage'
  assert torch.isfinite(mean).all() and torch.isfinite(std).all() and torch.all(std>=.05)
  checks.append({'rotation':rot['rotation'],'train_histories':len(train),'train_configs':1632,'held_out_normalization_invariant':True});tested.extend(test.tolist())
 assert sorted(tested)==list(range(2080))
 model=mod.Transition();assert sum(p.numel() for p in model.parameters())==5796
 # Synthetic inference only; no gradients, fitting, or real held-out predictions.
 with torch.no_grad():
  history=torch.randn(4,4,4);external=torch.randn(4,9);external[:,-1]=1
  pred=model(history,external);assert torch.equal(pred,history[:,-1])
  x=torch.randn(4,12,25);whole,_=model.cell(x);memory=None;parts=[]
  for j in range(12):
   y,memory=model.cell(x[:,j:j+1],memory);parts.append(y)
  assert torch.allclose(torch.cat(parts,1),whole,atol=2e-6,rtol=2e-5)
 report={'passed':True,'histories':2080,'rotations':checks,'test_partition_exactly_once':True,'parameters':5796,'synthetic_zero_head_persistence':True,'synthetic_prefix_equivalence':True,'training':False,'held_out_model_evaluation':False,'sequences_sha256':hashlib.sha256((R/'data/learning/sequences.npz').read_bytes()).hexdigest(),'remaining':'Cloud CUDA backward32/determinism, full reporting, optimizer/RNG checkpoint replay and measured runtime within budget remain mandatory. CPU data checks alone do not authorize skipping cloud preflight.'}
 (R/'results/model-data-preflight.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rotations'}))
if __name__=='__main__':main()
