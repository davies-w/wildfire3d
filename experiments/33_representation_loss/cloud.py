import json,subprocess
from pathlib import Path
R=Path(__file__).parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],text=True,capture_output=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def read(n):return json.loads((R/n).read_text())
def save(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n')
