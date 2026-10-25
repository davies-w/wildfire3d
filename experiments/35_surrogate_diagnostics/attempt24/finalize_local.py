"""Finish local preservation/analysis only; never publishes to Hugging Face or launches compute."""
from pathlib import Path
import json,hashlib,subprocess,time,fcntl,yaml
R=Path(__file__).resolve().parent;repo=R.parents[2];py=repo/'.venv/bin/python';dvc=repo/'.venv/bin/dvc'
def run(args):subprocess.run([str(x) for x in args],cwd=repo,check=True)
def main():
 with (R/'data/local-finalize.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while not (R/'results/collected.json').exists():time.sleep(30)
  assert json.loads((R/'results/collected.json').read_text())['complete']
  assert not any(json.loads((R/'results/cleanup.json').read_text()).values())
  assert json.loads((R/'results/permission-removed.json').read_text())['removed']
  manifest=json.loads((R/'data/collected/manifest.json').read_text())
  for name,digest in manifest.items():assert hashlib.sha256((R/'data/collected'/name).read_bytes()).hexdigest()==digest,name
  assert sum(n.endswith('-selected.pt') for n in manifest)==20
  proof=dict(complete=True,files=len(manifest),selected_models=20,checkpoints=sum(n.endswith('.pt') for n in manifest),sha256_verified=True,public_archive='Pending explicit approval after automatic review rejected publication')
  (R/'results/local-archive-verification.json').write_text(json.dumps(proof,indent=2))
  path=R/'dvc.yaml';d=yaml.safe_load(path.read_text());d['stages']['scorecard']={'cmd':'../../../.venv/bin/python scorecard_summary.py && ../../../.venv/bin/python audit_scorecard.py && ../../../.venv/bin/python render_scorecard.py','deps':['scorecard_summary.py','audit_scorecard.py','render_scorecard.py','data/sequences.npz','data/collected','../scorecard-v1.json'],'outs':['data/scorecard'],'metrics':[{'results/scorecard-summary.json':{'cache':False}},{'results/scenario-audit.json':{'cache':False}}]};path.write_text(yaml.safe_dump(d,sort_keys=False))
  run([dvc,'commit','-f',str(path)+':analysis']);run([dvc,'repro','--single-item',str(path)+':scorecard'])
  run([dvc,'push','-r','mirror',str(path)+':cloud_collect',str(path)+':analysis',str(path)+':scorecard'])
  run(['git','add',R,repo/'experiments/33_representation_loss/budget.json',repo/'docs/billing-audit-2026-10-23/runtime-reconciliation.json',repo/'docs/billing-audit-2026-10-23/vm-runtime.json'])
  run(['git','commit','-m','Preserve completed gated comparison and frozen scorecard diagnostics']);run(['git','push'])
  (R/'results/local-finalization-complete.json').write_text(json.dumps(dict(complete=True,public_upload=False,time_unix=time.time()),indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:(R/'results/local-finalization-error.json').write_text(json.dumps(dict(error=repr(e))));raise
