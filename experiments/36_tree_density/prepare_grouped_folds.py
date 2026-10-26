"""Freeze the approved ten-fold reshuffle from configuration identities only. No fitting."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parent
SEED=20261026

def main():
 oldpath=R.parent/'35_surrogate_diagnostics/attempt20/schema.json'
 old=json.loads(oldpath.read_text())['cases'];new=json.loads((R/'cases.json').read_text())
 cases=[{'case':c['case'],'source':'existing520','physical_key':c['physical_key']} for c in old]
 cases += [{'case':c['case'],'source':'density36','physical_key':[c[k] for k in ('crown_height_m','moisture','loading_multiplier','wind_speed','angle_deg')]} for c in new]
 assert len(cases)==2080 and len({c['case'] for c in cases})==2080
 keys=[tuple(c['physical_key']) for c in cases];unique=sorted(set(keys));assert len(unique)==2040
 assert not set(keys[:520]) & set(keys[520:])
 order=np.random.default_rng(SEED).permutation(len(unique));assignment={unique[int(j)]:int(i%10) for i,j in enumerate(order)}
 for c,k in zip(cases,keys):c['fold']=assignment[k]
 rotations=[]
 for test in range(10):
  valid=(test+1)%10
  row={'rotation':test,'test_fold':test,'validation_fold':valid,'train':[i for i,c in enumerate(cases) if c['fold'] not in (test,valid)],'validation':[i for i,c in enumerate(cases) if c['fold']==valid],'test':[i for i,c in enumerate(cases) if c['fold']==test]}
  partitions=[set(keys[i] for i in row[k]) for k in ('train','validation','test')]
  assert all(not partitions[i]&partitions[j] for i in range(3) for j in range(i))
  assert sum(len(row[k]) for k in ('train','validation','test'))==2080
  rotations.append(row)
 report={'seed':SEED,'method':'Sorted physical configuration keys, NumPy default_rng permutation, round-robin assignment to ten folds; replicas stay together. Assignment uses identities only, no outcomes.','histories':2080,'configurations':2040,'cases':cases,'rotations':rotations,'groups_per_fold':[sum(f==i for f in assignment.values()) for i in range(10)],'histories_per_fold':[sum(c['fold']==i for c in cases) for i in range(10)],'old_schema_sha256':hashlib.sha256(oldpath.read_bytes()).hexdigest(),'new_cases_sha256':hashlib.sha256((R/'cases.json').read_bytes()).hexdigest(),'training':False,'warning':'Previously examined dataset, not historically pristine. Full verified 1560 new histories are mandatory before model fitting; this manifest does not assert data completion.'}
 dest=R/'data/grouped-folds.json'
 if dest.exists():assert json.loads(dest.read_text())==report,'Existing frozen assignment differs'
 else:dest.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('seed','histories','configurations','groups_per_fold','histories_per_fold','training')}))
if __name__=='__main__':main()
