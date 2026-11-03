"""Offline regression against pinned cloud logs; never invokes FDS or an optimizer."""
import json,hashlib,tempfile
from pathlib import Path
from pilot_worker06 import stopped_log_progress
R=Path(__file__).resolve().parent
Q=R/'private-stopcheck01';base=Q/'archive/probe/tree48_000830_fine'
records={x['name']:x for x in json.loads((Q/'archive-proof.json').read_text())['objects']}
paths=[base/'diagnostic/first/run-1793689892513053355.log',base/'diagnostic/restored/run-1793690512293764593.log']
for p in paths:
 key='tree48/stopcheck01/'+p.relative_to(Q/'archive').as_posix()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==records[key]['sha256']
a=stopped_log_progress(paths[0]);b=stopped_log_progress(paths[1],a)
assert a==(30,1.16279) and b==(45,1.83706)
# Regression: inherited output, missing clean stop, and reversed progress must fail.
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'run.log'
 for text,previous in [(paths[0].read_text(),a),(paths[1].read_text().replace('STOP: FDS stopped by user',''),a),('Time Step: 32, Simulation Time: 1.3 s\nTime Step: 31, Simulation Time: 1.2 s\nSTOP: FDS stopped by user',a)]:
  p.write_text(text)
  try:stopped_log_progress(p,previous)
  except AssertionError:pass
  else:raise AssertionError('Invalid evidence was accepted')
print(json.dumps(dict(passed=True,first_progress=a,resumed_progress=b,negative_checks=3,local_solver_executed=False,scope='Offline log-checker regression; original cloud Batch result remains FAILED')))
