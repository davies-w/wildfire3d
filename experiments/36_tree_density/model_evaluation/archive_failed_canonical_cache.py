"""Preserve the failed strict-cache attempt before changing its numerical comparison policy."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1];source=R/'model_evaluation/prepare_canonical_feature_cache.py';old=R/'data/canonical-feature-cache';dest=R/'data/canonical-feature-cache-attempt01'
assert not dest.exists() and not (R/'results/canonical-feature-cache-prepared.json').exists();p=json.loads((old/'progress.json').read_text());assert list(p['origins'])==['0'];assert hashlib.sha256(source.read_bytes()).hexdigest()==p['source_sha256'][str(source.relative_to(R))]
for name,key in [('features.npy','features'),('base-states.npy','base')]:
 a=np.load(old/name,mmap_mode='r');assert hashlib.sha256(a[:,:45].tobytes()).hexdigest()==p['origins']['0'][key]
(old/'prepare-source.py').write_bytes(source.read_bytes());old.rename(dest)
proof=dict(passed=True,preserved_completed_origins=[0],failed_origin=1,reason='Old per-feature tolerance exceeded by19values in9histories; independent original-prefix replay identifies batch-layout numerical differences. No training or scientific score accepted from this partial cache.',original_source_sha256=p['source_sha256'][str(source.relative_to(R))],partial_arrays_and_source_preserved=True)
(R/'results/canonical-cache-attempt01-preserved.json').write_text(json.dumps(proof,indent=2)+'\n');print('Failed attempt preserved without overwriting partial evidence')
