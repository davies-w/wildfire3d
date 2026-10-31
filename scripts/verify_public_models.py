"""Fail closed on finance/credentials and verify exported model/data inventory."""
from pathlib import Path
import json,re,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'experiments/38_history8_shared64/data/project-model-archive'
m=json.loads((D/'manifest.json').read_text());bad=[]
financial=re.compile(r'budget|cost|spend|reserv|allowance|billing|invoice|usd|price|\$\s*\d',re.I)
sensitive={'private_key','privatekey','client_secret','secret_access_key','aws_secret_access_key','access_token','refresh_token','password','api_key'}
def walk(x,path):
 if isinstance(x,dict):
  for k,v in x.items():
   if financial.search(k):bad.append((path,'financial key'))
   if k.lower() in sensitive and v not in [None,'',False]:bad.append((path,'credential key'))
   walk(v,path)
 elif isinstance(x,list):
  for v in x:walk(v,path)
for row in m['files']:
 p=D/row['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
 if p.suffix=='.json':walk(json.loads(b),row['path'])
 if p.suffix in {'.pt','.pth','.pkl','.pickle','.joblib'}:
  parts=[]
  if zipfile.is_zipfile(p):
   with zipfile.ZipFile(p) as z:parts=[z.read(n) for n in z.namelist() if n.endswith('.pkl')]
  else:parts=[b]
  for part in parts:
   if re.search(rb'(?i)(private_key|client_secret|aws_secret_access_key|maximum_allowance_usd|estimated_spend_usd|budget_cap_usd)',part):bad.append((row['path'],'sensitive checkpoint metadata'))
assert not bad,str(bad[:20])
print(json.dumps({'passed':True,'files':len(m['files']),'experiments':len(m['experiments']),'model_files':sum(Path(x['path']).suffix in {'.pt','.pth','.safetensors','.pkl','.pickle','.joblib'} for x in m['files']),'array_files':sum(Path(x['path']).suffix in {'.npy','.npz'} for x in m['files'])}),flush=True)
