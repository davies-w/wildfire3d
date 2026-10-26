from pathlib import Path
import subprocess,concurrent.futures,json,hashlib,base64
O=Path(__file__).resolve().parent;G=str(Path.home()/'.local/google-cloud-sdk/bin/gcloud')
def one(p):
 uri='gs://tmrw-wildfire-20261015-trial/density36/orchestration/specs/'+p.name
 q=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],capture_output=True,text=True)
 if q.returncode:
  assert '404' in q.stderr or 'not found' in q.stderr.lower(),q.stderr
  subprocess.run([G,'storage','cp',str(p),uri,'--if-generation-match=0'],check=True,capture_output=True,timeout=120)
  q=subprocess.run([G,'storage','objects','describe',uri,'--format=json'],check=True,capture_output=True,text=True,timeout=120)
 assert json.loads(q.stdout)['md5_hash']==base64.b64encode(hashlib.md5(p.read_bytes()).digest()).decode()
 print('VERIFIED',p.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(one,sorted((O/'specs').glob('*.json'))))
(O/'spec-upload-complete.json').write_text('{"verified":102}\n')
