"""Select reviewed numerical epoch/baseline records; exclude operational metadata."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'experiments/51_three_tree_campaign/private07'
r=json.loads((p/'historical-45-46-metadata-review.json').read_text());rows=[x for x in r['files'] if re.fullmatch(r'fold\d+-(?:epoch\d+|baseline|checkpoint-replay)\.json',Path(x['path']).name)]
(p/'historical-training-metrics-policy-review.json').write_text(json.dumps({'files':rows,'excluded':[],'private_operational_records_not_selected':len(r['files'])-len(rows),'private_policy_exclusions':len(r['excluded'])},indent=2)+'\n');print('Selected',len(rows))
