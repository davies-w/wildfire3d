from pathlib import Path
import numpy as np,json,shutil,hashlib
R=Path(__file__).resolve().parent
P=json.loads((R/'coverage-plan.json').read_text());rng=np.random.default_rng(P['learning_curve']['split_seed'])
a=np.load(R.parent/'attempt24/data/sequences.npz');meta=json.loads((R.parent/'attempt24/schema.json').read_text())
rotation=int(rng.integers(10));original=meta['rotations'][rotation]
folds=a['fold'];trainfolds=sorted(set(int(folds[i]) for i in original['train']));order=rng.permutation(trainfolds).tolist()
rotations=[]
for n in range(1,9):
 train=[i for i in original['train'] if int(folds[i]) in order[:n]]
 rotations.append(dict(rotation=rotation,training_fold_count=n,training_folds=order[:n],train=train,validation=original['validation'],test=original['test'],unused=[i for i in original['train'] if i not in train]))
meta.update(rotations=rotations,comparison='Plain four-state GRU nested training-size learning curve',learning_curve=dict(seed=P['learning_curve']['split_seed'],rotation=rotation,training_fold_order=order,validation_fold=int(folds[original['validation'][0]]),test_fold=int(folds[original['test'][0]])),scorecard_sha256=hashlib.sha256((R.parent/'scorecard-v1.json').read_bytes()).hexdigest())
shutil.copyfile(R.parent/'attempt24/data/sequences.npz',R/'data/sequences.npz')
(R/'schema.json').write_text(json.dumps(meta,indent=2))
print(meta['learning_curve']);print([(x['training_fold_count'],len(x['train'])) for x in rotations])
