"""Prepare a new cloud-only curriculum branch from the selected complete checkpoint."""
from pathlib import Path
import hashlib, json, shutil
import torch
R = Path(__file__).resolve().parent
BASE = R.parent / '38_history8_shared64'
D = R / 'data/training'
assert not (R / 'results/submission-intent.json').exists(), 'Submitted inputs are immutable'
D.mkdir(parents=True, exist_ok=True)
source = BASE / 'data/training08'
checkpoint = BASE / 'data/training08-results/fold00-epoch109.pt'
ck = torch.load(checkpoint, map_location='cpu', weights_only=False)
assert ck['epoch'] == ck['best_epoch'] == 109
assert ck['optimizer']['state'] and ck['rng'] and len(ck['history']) == 110
assert ck['schema_hash'] == hashlib.sha256((source / 'schema.json').read_bytes()).hexdigest()
for name in ['worker.py', 'model.py', 'plain_model.py', 'gated_model.py', 'objective.py', 'runtime.py', 'schema.json', 'data/sequences.npz']:
    dest = D / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, dest)
p = json.loads((source / 'coverage-plan.json').read_text())
p.pop('budget', None)
p.update(experiment='39 selected epoch109 continuation: 64 then full sequence', minimum_epochs=160, sequence_horizon_steps=90)
p['horizon_curriculum'] += [{'first_epoch': 110, 'steps': 64}, {'first_epoch': 130, 'steps': 90}]
p['continuation'] = {'parent_experiment': 38, 'epoch': 109, 'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(), 'new_training_starts_at': 110, 'full_sequence_first_epoch': 130, 'selection': 'Best validation score including restored parent; no forced improvement claim'}
(D / 'coverage-plan.json').write_text(json.dumps(p, indent=2) + '\n')
w = (D / 'worker.py').read_text()
w = w.replace("P['budget']['soft_seconds']", "int(os.environ['TRAINING_SOFT_SECONDS'])")
w = w.replace("if epoch in [21,41,61]:", "if epoch in [s['first_epoch'] for s in P['horizon_curriculum']][1:]:")
w = w.replace('elif epoch>61:', "elif epoch>P['horizon_curriculum'][-1]['first_epoch']:")
(D / 'worker.py').write_text(w)
runtime = (D / 'runtime.py').read_text().replace('history38/training08/', 'longwindow39/training01/')
(D / 'runtime.py').write_text(runtime)
resume = D / 'data/resume'
resume.mkdir(parents=True, exist_ok=True)
shutil.copy2(checkpoint, resume / 'fold00.pt')
archive = resume / 'archive'
archive.mkdir(exist_ok=True)
for f in (BASE / 'data/training08-results').glob('fold00-*'):
    if f.name in ['fold00-baseline.json', 'fold00-checkpoint-replay.json'] or (f.name.startswith('fold00-epoch') and int(f.stem.split('epoch')[1]) <= 109):
        shutil.copy2(f, archive / f.name)
assert not (resume / 'fold00-report.json').exists(), 'A finished parent report would skip new training'
manifest = {str(f.relative_to(D)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(D.rglob('*')) if f.is_file() and f.name != 'hashes.json'}
(D / 'hashes.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Prepared checkpoint109 continuation; {len(manifest)} files; no training or optimizer updates executed')
