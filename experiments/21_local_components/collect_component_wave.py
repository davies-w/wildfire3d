"""One pass: collect named existing jobs, then extract/audit any newly completed case."""
import json,subprocess,sys
from scene import ROOT
names=sys.argv[1:];assert names
subprocess.run([sys.executable,str(ROOT/'component_control.py'),'collect',*names],check=True)
for name in names:
 if not (ROOT/'results'/f'{name}-collected.json').exists():continue
 if not (ROOT/'data/component_states'/f'{name}.json').exists():subprocess.run([sys.executable,str(ROOT/'extract_component_states.py'),name],check=True)
 if not (ROOT/'results'/f'{name}-audit.json').exists():subprocess.run([sys.executable,str(ROOT/'audit_component_runs.py'),name],check=True)
subprocess.run([sys.executable,str(ROOT/'reconcile_component_ledger.py')],check=True)
