"""Freeze ten environment-group folds without looking at outcome values."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parent

def main():
 source=json.loads((R/'data/source-schema.json').read_text());cases=source['cases'];groups={}
 for i,c in enumerate(cases):groups.setdefault(tuple(c['environment']),[]).append(i)
 assert len(groups)==25
 rng=np.random.default_rng(3516);keys=list(sorted(groups));rng.shuffle(keys);keys.sort(key=lambda g:-len(groups[g]))
 capacities=[3,2]*4+[2,3];folds=[[] for _ in capacities];counts=[0]*10;used=[0]*10
 for g in keys:
  eligible=[j for j in range(10) if used[j]<capacities[j]]
  j=min(eligible,key=lambda j:(counts[j]/capacities[j],used[j],j));folds[j].extend(groups[g]);counts[j]+=len(groups[g]);used[j]+=1
 for j,ids in enumerate(folds):
  for i in ids:cases[i]['fold']=j
 split={'rotation':0,'train':sorted(sum(folds[:8],[])),'validation':sorted(folds[8]),'test':sorted(folds[9])}
 assert sorted(split['train']+split['validation']+split['test'])==list(range(len(cases)))
 for field in ['environment','physical_configuration']:
  sets=[{tuple(cases[i][field]) for i in split[s]} for s in ['train','validation','test']]
  assert all(not sets[i]&sets[j] for i in range(3) for j in range(i))
 source.update(rotations=[split],fold_policy={'seed':3516,'group':'wind_m_s and moisture_fraction; all scenarios with each environment stay together','fold_environment_counts':used,'fold_case_counts':counts,'selection':'Only case counts used; no outcome-based balancing or resampling','user_approved':'Ten approximately balanced grouped folds, one 8/1/1 rotation'})
 (R/'data/schema.json').write_text(json.dumps(source,indent=2)+'\n')
 print(json.dumps({s:len(split[s]) for s in ['train','validation','test']}));print('PASS group and physical-configuration separation')
if __name__=='__main__':main()
