"""Select only reviewed FDS boundary text exports, leaving operational JSON private."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'experiments/51_three_tree_campaign/private07'
r=json.loads((p/'historical-text-policy-review.json').read_text());selected=[]
for row in r['files']:
 f=ROOT/row['path']
 if f.name.startswith('ig_') and f.suffix=='.txt':
  assert not f.stat().st_size or f.read_text().startswith('Patch'),str(f)
  selected.append(row)
(p/'historical-boundary-text-policy-review.json').write_text(json.dumps({'files':selected,'excluded':[],'selection':'Only ig_*.txt FDS boundary exports; empty exports retained exactly','other_text_not_authorized_by_this_selection':len(r['files'])-len(selected),'policy_exclusions_retained_privately':len(r['excluded'])},indent=2)+'\n')
print('Selected',len(selected))
