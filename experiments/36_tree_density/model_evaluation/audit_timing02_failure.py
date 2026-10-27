"""Recheck archived preflight failure evidence; no cloud writes or compute."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
r=json.loads((R/'results/model-timing02-diagnosis.json').read_text())
root=R/'data/model-timing02-failure'
for n,h in r['evidence'].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h
assert json.loads((root/'report-equivalence.json').read_text())['passed']
assert 'cudnn RNN backward can only be called in training mode' in (root/'bootstrap-error.txt').read_text()
assert json.loads((root/'job-status.json').read_text())['status']['state']=='FAILED'
assert r['cleanup_verified'] and r['exact_read_grant_removed']
assert 'model.train()' in (R/'data/model-preflight03/time_cloud.py').read_text()
print('DIAGNOSED HARNESS MODE ERROR; EQUIVALENCE PASSED; NO SCIENCE CHANGE')
