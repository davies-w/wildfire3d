from pathlib import Path
import subprocess,json,hashlib,fcntl,time
R=Path(__file__).resolve().parent;P=R/'private';P.mkdir(exist_ok=True)
G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud');PROJECT='tmrw-wildfire-20261015';BUCKET=PROJECT+'-trial';PREFIX='tree48/pilot01/';WF='fds-tree48-pilot01';B=R.parent/'33_representation_loss/budget.json'
def gc(*args):
 p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True,timeout=240)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout or '{}')
def save(name,x):(P/name).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reserve():
 with (B.parent/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text())
  if WF in b['reservations']:return
  assert b['estimated_spend_usd']+b['reserved_usd']+20<=b['authorized_usd']
  b['reservations'][WF]=dict(state='reserved_before_build',allowance_usd=20,reserved_unix=time.time(),scope='24-case CPU pilot including cloud image build, bounded workers, disk, transfer and cleanup; zero automatic paid retries')
  b['reserved_usd']+=20;B.write_text(json.dumps(b,indent=2)+'\n');save('reservation.json',dict(key=WF,allowance_usd=20))
if __name__=='__main__':
 reserve();assert not (P/'build-intent.json').exists(),'Inspect existing build, never duplicate'
 import shutil,yaml
 d=R/'data/cloud-context';d.mkdir(exist_ok=True);src=R.parent/'16_code_profiling/data/binary/fds';assert sha(src)=='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
 shutil.copyfile(src,d/'fds');(d/'fds').chmod(0o755);shutil.copyfile(R.parent/'36_tree_density/repair/Dockerfile',d/'Dockerfile')
 build=yaml.safe_load((R.parent/'36_tree_density/repair/cloudbuild.yaml').read_text());build=json.loads(json.dumps(build).replace('solver36:restored','solver48:pilot01'));(R/'cloudbuild.yaml').write_text(yaml.safe_dump(build,sort_keys=False))
 save('build-intent.json',dict(time=time.time()));v=gc('builds','submit',str(d),'--config='+str(R/'cloudbuild.yaml'),'--async');save('build.json',v);print('Build submitted',v['id'])
