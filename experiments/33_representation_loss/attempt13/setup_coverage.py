"""Fixed-seed extra training coverage selected without looking at field targets."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).parent;S=R.parent.parent/'32_tree_expansion'
cs=json.loads((S/'development.json').read_text());pilot=[c for c in json.loads((R.parent/'attempt11/cases.json').read_text()) if c['split']=='train'];used={c['configuration'] for c in pilot};rng=np.random.default_rng(3313);train=list(pilot)
for height in [4,6,8,10]:
 pool=sorted([c for c in cs if c['new_geometry'] and c['split']=='train' and c['replica']==0 and c['crown_height_m']==height and c['configuration'] not in used],key=lambda c:c['case'])
 train += [pool[i] for i in rng.choice(len(pool),27,replace=False)]
val=[c for c in cs if c['new_geometry'] and c['split']=='validation'];chosen=train+val;assert len(train)==120 and len(val)==40 and len({c['configuration'] for c in chosen})==152
names={c['case'] for c in chosen};(R/'cases.json').write_text(json.dumps(chosen,indent=2));groups=json.loads((S/'groups.json').read_text());(R/'groups.json').write_text(json.dumps([g for g in groups if names.intersection(g['cases'])],indent=2));z=np.load(S/'data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{n:z[n] for n in names})
(R/'coverage-plan.json').write_text(json.dumps(dict(seed=3313,pilot_configurations=sorted(used),train_configurations=sorted(c['configuration'] for c in train),validation_configurations=sorted({c['configuration'] for c in val}),scope='120primary-seed trainingconfigs:12pilot plus108fixed-random balanced30perheight.32validationconfigs40trajectories. No field-target-based additional selection; all previously exp32development.'),indent=2))
