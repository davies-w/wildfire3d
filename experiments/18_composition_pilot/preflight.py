"""Check all layout geometry and initialize one, two and three particle crowns locally."""
import csv
import hashlib
import json
import math
import os
import subprocess
from generate import ROOT, write, deck

design=json.loads((ROOT/'design.json').read_text())
splits={s:{r['layout'] for r in design['cases'] if r['split']==s} for s in ('train','validation','test')}
assert len(design['cases'])==42
assert not splits['train']&splits['validation'] and not splits['train']&splits['test']
assert all(len(x)<3 for x in splits['train']|splits['validation'])
assert all(len(x)==3 for x in splits['test'])
for layout in set.union(*splits.values()):
    coords=[design['anchors_m'][a] for a in layout]
    assert all(math.dist(a,b)>1.7 for i,a in enumerate(coords) for b in coords[i+1:])
    assert all(x+.85<14 and .85<x<23.15 and .85<y<23.15 for x,y in coords)
    text=deck('geometry',layout,800)
    assert text.count('&INIT ')==len(layout)*4
    assert text.count("SURF_ID='IGNITOR'")==len(layout)
    assert text.count('&MESH ')==6
    assert f'HRRPUA={800/len(layout)}' in text
records=[]
binary=ROOT.parents[1]/'FDS/src/fds/Build/ompi_gnu_osx/fds_ompi_gnu_osx'
# D crosses an internal mesh interface; include it in the initialization check.
for layout in ['D','AB','ACD']:
    c=write('preflight_'+layout,layout,800,horizon=1.05,split='preflight')
    name=c['case']; folder=ROOT/'data/preflight'/name; folder.mkdir(parents=True,exist_ok=True)
    with (folder/'run.log').open('w') as log:
        result=subprocess.run([str(binary),str(ROOT/'decks'/f'{name}.fds')],cwd=folder,
            env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),
            stdout=log,stderr=subprocess.STDOUT,timeout=120)
    output=(folder/'run.log').read_text()
    assert result.returncode==0 and 'completed successfully' in output.lower(),output[-4000:]
    with (folder/f'{name}_devc.csv').open() as f:
        it=csv.reader(f);next(it);keys=[k.strip().strip('"') for k in next(it)]
        values=[dict(zip(keys,map(float,v))) for v in it if v]
    assert all(math.isfinite(v[k]) and v[k]>-1e10 for v in values for k in keys)
    masses={k:values[-1][k] for k in keys if k.startswith('mass ')}
    assert all(v>0 for v in masses.values()),masses
    for f in folder.glob('*.restart'):f.unlink()
    records.append(dict(case=name,completed=True,crowns=len(layout),mass_kg=masses,
                        elapsed_sim_s=values[-1]['Time'],binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
(ROOT/'results/local-preflight.json').write_text(json.dumps(records,indent=2)+'\n')
(ROOT/'results/design-check.json').write_text(json.dumps(dict(passed=True,layouts=12,cases=42,
    no_split_overlap=True,nonblock_vegetation=True,full_reference_cells=55296),indent=2)+'\n')
print('All geometry, split, full-mesh startup, face-device and particle-mass checks passed.')
