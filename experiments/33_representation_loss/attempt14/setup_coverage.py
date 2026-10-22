"""Use all existing new-geometry primary training configurations; no target selection."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;S=R.parent.parent/'32_tree_expansion'
cs=json.loads((S/'development.json').read_text());train=[c for c in cs if c['new_geometry'] and c['split']=='train' and c['replica']==0];val=[c for c in cs if c['new_geometry'] and c['split']=='validation'];chosen=train+val
assert len(train)==360 and len(val)==40 and len({c['configuration'] for c in chosen})==392
names={c['case'] for c in chosen};(R/'cases.json').write_text(json.dumps(chosen,indent=2));groups=json.loads((S/'groups.json').read_text());(R/'groups.json').write_text(json.dumps([g for g in groups if names.intersection(g['cases'])],indent=2));z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in names})
reference=json.loads((R.parent/'attempt13/coverage-plan.json').read_text())['train_configurations'];assert len(reference)==120
(R/'coverage-plan.json').write_text(json.dumps(dict(reference_configurations=reference,train_configurations=sorted(c['configuration'] for c in train),validation_configurations=sorted({c['configuration'] for c in val}),scope='360primary-seed newgeometry trainingconfigs versus reference120;32validationconfigs40trajectories. Legacy40training and8validation omitted; seedreplicas used in validation only. Previously exp32development, not pristine test.'),indent=2))
