import json,hashlib,shutil
from pathlib import Path
from scipy.stats import qmc
R=Path(__file__).parent;P=R.parent/'27_single_tree_cnn'
for d in ['decks','jobs','data/cloud','data/downloads']:(R/d).mkdir(exist_ok=True)
for n in ['build.py','legacy_build.py','base-input.fds','reference-particles.json','fields.py','worker.py','runner-template.py','workflow-template.json']:shutil.copy2(P/n,R/n)
shutil.copy2(P/'data/tree-templates.json',R/'data/tree-templates.json')
import build
old=json.loads((P/'cases.json').read_text());development=[c for c in old if c['split'] in ['train','validation']];tests=[];ts=json.loads((R/'data/tree-templates.json').read_text())
for i,(u,v) in enumerate(qmc.Sobol(2,scramble=True,seed=2804).random_base2(3)[:6]):
 c=dict(next(c for c in old if c['split']=='train'));c.update(case=f's28_test_{i}',split='test',wind_speed=float(1+4*u),angle_deg=float(360*v),training_rank=i)
 assert not any((c['wind_speed'],c['angle_deg'])==(q['wind_speed'],q['angle_deg']) for q in old)
 deck,_=build.deck(c,ts);c['deck_sha256']=hashlib.sha256(deck.encode()).hexdigest();(R/'decks'/f"{c['case']}.fds").write_text(deck);tests.append(c)
(R/'cases.json').write_text(json.dumps(development+tests,indent=2));(R/'results/input-freeze.json').write_text(json.dumps(dict(template_sha256=hashlib.sha256((R/'data/tree-templates.json').read_bytes()).hexdigest(),cases={c['case']:c['deck_sha256'] for c in tests}),indent=2));print('Six fresh test conditions prepared; no submissions')
