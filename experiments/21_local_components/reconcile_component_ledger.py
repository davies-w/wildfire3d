"""Mark hash-verified, cleaned collected jobs complete. Never alter reservations."""
import json,fcntl
from scene import ROOT
p=ROOT/'budget-overnight.json'
with (ROOT/'data/overnight-budget.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);d=json.loads(p.read_text());old=d['reserved_usd'];changed=[]
 for name,r in d['reservations'].items():
  proof=ROOT/'results'/f'{name}-collected.json'
  if r['state']!='submitted' or not proof.exists():continue
  a=json.loads(proof.read_text())
  if any(a['cleanup'].values()) or not a.get('checkpoint_files_verified'):continue
  if a['result']['deck_sha256']!=r['case']['sha256']:continue
  if a['result'].get('returncode')==0 and a['result'].get('full_horizon'):r['state']='completed_cleanup_verified';changed.append(name)
 assert d['reserved_usd']==old;p.write_text(json.dumps(d,indent=2));print('Reconciled',changed,'reserved unchanged',old)
