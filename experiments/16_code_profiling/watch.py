"""Read-only wait for this trial; run final local analysis after its controller ends."""
import subprocess,time,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
while True:
 subprocess.run([sys.executable,str(ROOT/'fetch.py')],check=True)
 subprocess.run([sys.executable,str(ROOT/'status.py')],check=True)
 status=json.loads((ROOT/'results/workflow-status.json').read_text())
 if status['state']!='ACTIVE':break
 time.sleep(60)
for script in ['analyze.py','symbolize.py','boundary.py','ignition_boundary.py','geometry.py','plot.py']:
 subprocess.run([sys.executable,str(ROOT/script)],check=True)
print('Final evidence downloaded, analyzed, and cleanup checked.',flush=True)
