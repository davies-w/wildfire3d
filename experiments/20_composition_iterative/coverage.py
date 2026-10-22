"""Summarize only raw-boundary-verified development batch outcomes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'batches/development20/results/diagnosis.json'
rows=json.loads(p.read_text())['cases'];spec=json.loads((ROOT/'batches/development20/batch.json').read_text())
assert all(r['all_house_boundary_burning_rate']['device_label_agrees'] for r in rows)
report=dict(completed=len(rows),planned=len(spec['cases']),positives=sum(r['ignited'] for r in rows),negatives=sum(not r['ignited'] for r in rows),
 positive_training_geometries=sorted({r['layout'] for r in rows if r.get('split')=='train' and r['ignited']}),
 by_layout={l:dict(completed=sum(r['layout']==l for r in rows),positives=sum(r['layout']==l and r['ignited'] for r in rows)) for l in sorted({r['layout'] for r in rows})},
 training_ready=False,note='Partial batch progress only. Final assembly and coverage checks precede fitting; no test outcomes read.')
(ROOT/'results/development-progress.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
