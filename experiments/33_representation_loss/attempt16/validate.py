"""No fitting: schema, hash, schedule and model interface checks."""
import ast,json,hashlib
from pathlib import Path
import numpy as np,torch
from geometry_model import GeometryCNN
from worker_base import predict
R=Path(__file__).parent
plan=json.loads((R/'coverage-plan.json').read_text());cs=json.loads((R/'cases.json').read_text());assert len(cs)==52 and len(plan['models'])==52
assert len([c for c in cs if c['split']=='train'])==12 and len([c for c in cs if c['split']=='validation'])==40
assert all(c['split']!='test' for c in cs)
for x in plan['models']:assert hashlib.sha256((R/'data/resume'/x['file']).read_bytes()).hexdigest()==x['sha256']
for p in R.glob('*.py'):ast.parse(p.read_text())
assert 'opt.step' not in (R/'worker.py').read_text() and '.backward(' not in (R/'worker.py').read_text()
torch.set_num_threads(2);m=GeometryCNN();state=torch.load(R/'data/resume'/plan['models'][0]['file'],map_location='cpu',weights_only=False);m.load_state_dict(state['model']);z=np.load(R/'data/geometries.npz')
with torch.no_grad():
 p=predict(m,'current',cs[0],np.array([0.,60.],dtype=np.float32),z[cs[0]['case']],'cpu');assert p.shape==(2,6,48,32,32) and torch.isfinite(p).all()
(R/'results/preflight.json').write_text(json.dumps(dict(passed=True,checkpoints=52,cases=52,no_training=True,hashes_checked=True),indent=2));print('EVALUATION PREFLIGHT PASSED')
