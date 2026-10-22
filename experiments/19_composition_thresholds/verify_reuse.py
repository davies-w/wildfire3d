"""Verify reusable external evidence without running FDS or revealing new test data."""
import hashlib
import json
import tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
design=json.loads((ROOT/'design.json').read_text())
archive=ROOT/'data/reused-evidence.tar.gz'
with tarfile.open(archive) as t:
    for row in design['reuse']:
        raw=t.extractfile('cloud/'+row['case']+'/result.json').read()
        assert hashlib.sha256(raw).hexdigest()==row['result_sha256']
        result=json.loads(raw)
        assert result['full_horizon'] and result['returncode']==0
        assert result['deck_sha256']==row['deck_sha256']
        if row['role']=='train':assert len(row['layout'])<=2
        if row['role']=='bracket_only':assert len(row['layout'])==3
counts={role:sum(r['role']==role for r in design['reuse']) for role in ['train','validation','bracket_only']}
(ROOT/'results/reuse-check.json').write_text(json.dumps(dict(passed=True,counts=counts,
    archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2)+'\n')
print('Verified reusable completed evidence:',counts)
