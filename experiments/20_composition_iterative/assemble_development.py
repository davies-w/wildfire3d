"""Assemble eligible completed evidence; no bare controls or test outcomes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
assert not (ROOT/'results/frozen-weights.json').exists(),'Do not alter development evidence after freezing'
rows=json.loads((ROOT/'reuse-manifest.json').read_text())
for batch in ('diagnostic01','exposure01','development20'):
    base=ROOT/'batches'/batch
    campaign=json.loads((base/'data/cloud/campaign.json').read_text())
    assert campaign['status']=='complete',batch
    for spec in json.loads((base/'batch.json').read_text())['cases']:
        if spec.get('vegetation',spec['layout'])!=spec['layout']:continue
        result=json.loads((base/'data/cloud'/spec['case']/'result.json').read_text())
        assert result['full_horizon'] and result['returncode']==0
        rows.append(dict(case=spec['case'],layout=spec['layout'],total_source_kw=spec['total_source_kw'],duration_s=result['duration_s'],seed=result['seed'],
            split='validation' if spec['layout'] in ('AC','AD','AF') else 'train',folder=str((base/'data/cloud'/spec['case']).relative_to(ROOT))))
assert len({r['case'] for r in rows})==len(rows)
assert not ({r['layout'] for r in rows if r['split']=='train'}&{r['layout'] for r in rows if r['split']=='validation'})
(ROOT/'development-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Assembled',len(rows),'development cases, excluding bare/partial controls.')
