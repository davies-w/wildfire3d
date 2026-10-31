"""Fail closed on finance/credentials and verify exported model/data inventory."""
from pathlib import Path
import json,re,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'experiments/38_history8_shared64/data/project-model-archive'
m=json.loads((D/'manifest.json').read_text());bad=[]
financial=re.compile(r'budget|cost|spend|reserv|allowance|billing|invoice|usd|price|\$\s*\d',re.I)
sensitive={'private_key','privatekey','client_secret','secret_access_key','aws_secret_access_key','access_token','refresh_token','password','api_key'}
def check_pairs(pairs):
 for k,v in pairs:
  if financial.search(k):bad.append((current,'financial key'))
  if k.lower() in sensitive and v not in [None,'',False]:bad.append((current,'credential key'))
 return dict(pairs)
for idx,row in enumerate(m['files']):
 if idx%10000==0:print('Privacy-verified files',idx,flush=True)
 p=D/row['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
 if p.suffix=='.json':
  current=row['path'];json.loads(b,object_pairs_hook=check_pairs)
 if p.suffix in {'.pt','.pth','.pkl','.pickle','.joblib'}:
  parts=[]
  if zipfile.is_zipfile(p):
   with zipfile.ZipFile(p) as z:parts=[z.read(n) for n in z.namelist() if n.endswith('.pkl')]
  else:parts=[b]
  for part in parts:
   lower=part.lower()
   if any(needle in lower for needle in [b'private_key',b'client_secret',b'aws_secret_access_key',b'maximum_allowance_usd',b'estimated_spend_usd',b'budget_cap_usd']):bad.append((row['path'],'sensitive checkpoint metadata'))
assert not bad,str(bad[:20])
print(json.dumps({'passed':True,'files':len(m['files']),'experiments':len(m['experiments']),'model_files':sum(Path(x['path']).suffix in {'.pt','.pth','.safetensors','.pkl','.pickle','.joblib'} for x in m['files']),'array_files':sum(Path(x['path']).suffix in {'.npy','.npz'} for x in m['files'])}),flush=True)
