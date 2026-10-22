"""Startup validation only; no cloud submission or physical validation."""
import json,os,subprocess
from pathlib import Path
from scene import ROOT
from sampling_test import BINARY

def run():
 report=[]
 for c in json.loads((ROOT/'results/overnight-grid-candidates.json').read_text())['cases']:
  name=c['case'];folder=ROOT/'data/overnight_grid_preflight'/name;folder.mkdir(parents=True,exist_ok=True)
  source=(ROOT/c['path']).read_text().replace('T_END=40','T_END=.1').replace('DT_RESTART=10.','DT_RESTART=100000.')
  deck=folder/'check.fds';deck.write_text(source)
  with (folder/'run.log').open('w') as f:p=subprocess.run([str(BINARY),str(deck)],cwd=folder,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=240)
  passed=p.returncode==0 and 'completed successfully' in (folder/'run.log').read_text().lower()
  report.append(dict(case=name,passed=passed,scope='0.1s native startup/output quantity checks only; no ignition or Linux-resume conclusion'))
  (ROOT/'results/overnight-grid-preflight.json').write_text(json.dumps(report,indent=2))
  assert passed,name
 print(json.dumps(report),flush=True)
if __name__=='__main__':run()
