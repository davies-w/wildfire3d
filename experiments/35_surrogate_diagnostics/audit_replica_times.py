"""Read archived FDS slice times directly; no training or simulation."""
from pathlib import Path
import json,tarfile,tempfile,sys
import numpy as np
from fields import read_slice
R=Path(__file__).parent;archive=R.parent/'32_tree_expansion/data/cloud_archive';cs=json.loads((R/'cases.json').read_text());groups=json.loads((R/'groups.json').read_text());rows=[]
def times(c):
 g=next(g['id'] for g in groups if c['case'] in g['cases']);p=archive/g/(c['case']+'.tar.gz')
 with tarfile.open(p) as tar:
  member=next(m for m in tar if m.name.endswith('.sf'))
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'slice.sf';dest.write_bytes(tar.extractfile(member).read());return read_slice(dest)[3]
for cfg in sorted({c['configuration'] for c in cs if c['split']=='validation'}):
 pair=sorted([c for c in cs if c['configuration']==cfg],key=lambda c:c['replica'])
 if len(pair)<2:continue
 for other in pair[1:]:
  selected=[pair[0],other]
  a,b=map(times,selected);ids=np.abs(b[:,None]-a).argmin(0);delta=np.abs(b[ids]-a);rows.append(dict(configuration=cfg,cases=[c['case'] for c in selected],counts=[len(a),len(b)],exact_equal=np.array_equal(a,b),max_nearest_delta_s=float(delta.max()),distinct_mapping=len(set(ids.tolist()))==len(a),same_index_mapping=np.array_equal(ids,np.arange(len(a)))))
assert len(rows)==8
(R/'results/replica-time-audit.json').write_text(json.dumps(dict(rows=rows,max_delta_s=max(r['max_nearest_delta_s'] for r in rows),scope='Raw archived FDS slice timestamps; no resimulation or training.'),indent=2));print(json.dumps(rows,indent=2))
