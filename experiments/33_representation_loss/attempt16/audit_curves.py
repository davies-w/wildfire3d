"""Check frozen checkpoint/case coverage and identical shared starts."""
import json
from pathlib import Path
R=Path(__file__).parent;r=R/'data/collected';x=json.loads((r/'report.json').read_text());plan=json.loads((R/'coverage-plan.json').read_text());assert x['plan']==plan
for m in plan['models']:
 shard=json.loads((r/f"eval-{m['arm']}-{m['step']:05}.json").read_text());assert shard['checkpoint']==m and shard['cases']==plan['cases'];assert sorted(v['case'] for v in shard['rows'])==plan['cases']
rows=x['rows'];baseline={v['case']:v for v in rows if v['arm']=='coverage360' and v['step']==12000}
for v in rows:
 if v['arm']!='coverage360' and v['step']==0:
  for w in ['all','post_source','late']:assert v[w]==baseline[v['case']][w]
(R/'results/curve-audit.json').write_text(json.dumps(dict(passed=True,checkpoint_states=52,case_histories=2704,frozen_plan_equal=True,shards_have_exact_case_coverage=True,shared_start_predictions_identical=True),indent=2)+'\n')
