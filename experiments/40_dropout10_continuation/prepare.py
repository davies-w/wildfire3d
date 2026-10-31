"""Prepare a new cloud-only curriculum branch from the selected complete checkpoint."""
from pathlib import Path
import hashlib, json, shutil
import torch
R = Path(__file__).resolve().parent
BASE = R.parent / '39_long_window_continuation'
D = R / 'data/training'
assert not (R / 'results/submission-intent.json').exists(), 'Submitted inputs are immutable'
D.mkdir(parents=True, exist_ok=True)
source = BASE / 'data/training02'
checkpoint = BASE / 'data/pool02-results/fold00-epoch159.pt'
ck = torch.load(checkpoint, map_location='cpu', weights_only=False)
assert ck['epoch'] == ck['best_epoch'] == 159
assert ck['optimizer']['state'] and ck['rng'] and len(ck['history']) == 160
assert ck['schema_hash'] == hashlib.sha256((source / 'schema.json').read_bytes()).hexdigest()
for name in ['worker.py', 'model.py', 'plain_model.py', 'gated_model.py', 'objective.py', 'runtime.py', 'schema.json', 'data/sequences.npz']:
    dest = D / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, dest)
p = json.loads((source / 'coverage-plan.json').read_text())
p.pop('budget', None)
p.update(experiment='40 selected epoch159 continuation: shared SiLU dropout10%', minimum_epochs=190, sequence_horizon_steps=90, dropout_probability=0.1)
p['horizon_curriculum'] += [{'first_epoch': 160, 'steps': 90}]
p['continuation'] = {'parent_experiment': 39, 'epoch': 159, 'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(), 'new_training_starts_at': 160, 'selection': 'Best validation including restored parent; dropout off for evaluation'}
(D / 'coverage-plan.json').write_text(json.dumps(p, indent=2) + '\n')
w = (D / 'worker.py').read_text()
w = w.replace("P['budget']['soft_seconds']", "int(os.environ['TRAINING_SOFT_SECONDS'])")
w = w.replace("if epoch in [21,41,61]:", "if epoch in [s['first_epoch'] for s in P['horizon_curriculum']][1:]:")
w = w.replace('elif epoch>61:', "elif epoch>P['horizon_curriculum'][-1]['first_epoch']:")
# Deterministic serialization/backward checks are in eval mode. Actual train-mode
# dropout backward and RNG replay are tested by the cloud startup check.
w=w.replace("m=Transition(kind).to(device)", "m=Transition(kind).to(device);m.eval()")
w=w.replace("m2=Transition(kind).to(device);", "m2=Transition(kind).to(device);m2.eval();")
w=w.replace('exact_replay=True,backward32=True','exact_replay=True,backward32=True,mode="evaluation_dropout_disabled"')
(D / 'worker.py').write_text(w)
g=(D/'gated_model.py').read_text()
assert 'nn.Linear(64,64),nn.SiLU()' in g
g=g.replace('nn.Linear(64,64),nn.SiLU()', 'nn.Linear(64,64),nn.SiLU(),nn.Dropout(p=0.1)')
(D/'gated_model.py').write_text(g)
runtime = (D / 'runtime.py').read_text().replace('history38/training08/', 'longwindow39/training01/')
(D / 'runtime.py').write_text(runtime)
resume = D / 'data/resume'
resume.mkdir(parents=True, exist_ok=True)
shutil.copy2(checkpoint, resume / 'fold00.pt')
archive = resume / 'archive'
archive.mkdir(exist_ok=True)
for f in (BASE / 'data/pool02-results').glob('fold00-*'):
    if f.name in ['fold00-baseline.json', 'fold00-checkpoint-replay.json'] or (f.name.startswith('fold00-epoch') and int(f.stem.split('epoch')[1]) <= 159):
        shutil.copy2(f, archive / f.name)
assert not (resume / 'fold00-report.json').exists(), 'A finished parent report would skip new training'
manifest = {str(f.relative_to(D)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(D.rglob('*')) if f.is_file() and f.name != 'hashes.json'}
(D / 'hashes.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Prepared checkpoint159 continuation; {len(manifest)} files; no training or optimizer updates executed')
