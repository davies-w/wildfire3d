"""Synthetic plumbing check; no synthetic rows enter scientific datasets."""
import json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PYTHON=ROOT.parents[1]/'.venv/bin/python'
with tempfile.TemporaryDirectory(prefix='composition20-check-') as tmp:
    p=Path(tmp);(p/'data').mkdir();(p/'results').mkdir()
    for name in ('models.py','train.py','predict.py','evaluate.py','design.json'):shutil.copy2(ROOT/name,p/name)
    cfg=json.loads((ROOT/'training.json').read_text());cfg.update(epochs=10,seeds=[11]);(p/'training.json').write_text(json.dumps(cfg))
    rows=[]
    for split,layouts,repeats in [('train',['A','AB','AE'],8),('validation',['AC','AD'],4)]:
        for layout in layouts:
            for i in range(repeats):rows.append(dict(case=f'{split}_{layout}_{i}',layout=layout,split=split,duration_s=20,total_source_kw=300 if i%2==0 else 1700,target=[i%2,.5 if i%2 else 1.],auxiliary=[[0.]*12 for _ in range(5)]))
    (p/'data/development.json').write_text(json.dumps(rows))
    tests=[dict(case=f'test_{l}_{i}',layout=l,duration_s=20,total_source_kw=300 if i==0 else 1700) for l in ('ABC','ABG','ACG') for i in range(2)]
    (p/'confirmation-inputs.json').write_text(json.dumps(tests))
    for name in ('train.py','predict.py'):subprocess.run([str(PYTHON),name],cwd=p,check=True,capture_output=True,text=True)
    tests=[dict(r,target=[i%2,.5 if i%2 else 1.]) for i,r in enumerate(tests)];(p/'data/test.json').write_text(json.dumps(tests))
    subprocess.run([str(PYTHON),'evaluate.py'],cwd=p,check=True,capture_output=True,text=True)
    report=json.loads((p/'results/evaluation.json').read_text());assert report['coverage']['positives']==3
    result=dict(passed=True,synthetic_only=True,checks=['train with globally mixed classes and a held-out geometry split','freeze checkpoints','predict from initial conditions only','evaluate both classes and baselines'])
    (ROOT/'results/pipeline-check.json').write_text(json.dumps(result,indent=2)+'\n')
print('Synthetic train/predict/evaluate plumbing passed; no scientific results generated.')
