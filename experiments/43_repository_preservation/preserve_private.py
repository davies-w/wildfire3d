"""Preserve excluded originals and audit evidence to the local mirror only."""
from pathlib import Path
import json,shutil,re
R=Path(__file__).resolve().parent;ROOT=R.parents[1];D=R/'data/private';D.mkdir(parents=True,exist_ok=True)
secret=re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{25,}|AIza[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16}')
credential_keys={'private_key','client_secret','secret_access_key','aws_secret_access_key','access_token','refresh_token','password','api_key'}
def credential_value(x):
 if isinstance(x,dict):return any((k.lower() in credential_keys and bool(v)) or credential_value(v) for k,v in x.items())
 if isinstance(x,list):return any(credential_value(v) for v in x)
 return False
names=[]
for name in ['private-git-paths.json','additional-ledger-paths.json','untracked-metadata-inventory.json']:
 names+=json.loads((R/'results'/name).read_text())
for name in sorted(set(names)):
 p=ROOT/name
 if p.is_file():
  b=p.read_bytes()
  if secret.search(b):continue
  if p.suffix=='.json' and credential_value(json.loads(b)):continue
  d=D/'originals'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
shutil.copytree(R/'results',D/'audit',dirs_exist_ok=True)
print('Private originals and audit evidence retained locally; never a public upload target')
