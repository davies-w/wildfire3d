from pathlib import Path
import subprocess,json,hashlib,fcntl,time
R=Path(__file__).resolve().parent;P=R/'private07';P.mkdir(exist_ok=True)
G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud');PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial';PREFIX='tree51/t51r07/';WF='t51r07';RESERVATION='fds-tree51-campaign07';B=R.parent/'33_representation_loss/budget.json'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True,timeout=240)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def save(name,x):(P/name).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
