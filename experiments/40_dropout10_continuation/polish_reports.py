"""Normalize readable numeric spacing in new report prose, never URLs or old pages."""
from pathlib import Path
import re,json,hashlib
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;D=R/'data/report-public'
def readable(s):
 parts=re.split(r'(<[^>]+>)',s)
 for i in range(0,len(parts),2):
  t=parts[i];t=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',t);t=re.sub(r'([:;,])(?=[A-Za-z])',r'\1 ',t);t=re.sub(r':(?=\d)',': ',t);parts[i]=t
 return ''.join(parts)
proof=R/'results02/report-publication.json';p=json.loads(proof.read_text());api=HfApi();repo='wdavies/fire-reports';rev=api.repo_info(repo,repo_type='space').sha;assert rev==p['commit'];files={}
for slug in ['longwindow39','dropout40']:
 n=slug+'/index.html';f=D/n;old=f.read_bytes();assert Path(hf_hub_download(repo,n,repo_type='space',revision=rev)).read_bytes()==old;original=Path(hf_hub_download(repo,n,repo_type='space',revision=p.get('initial_commit',rev))).read_text();css=re.search(r'<style>.*?</style>',original,re.S)[0];text=re.sub(r'<style>.*?</style>',lambda _:css,old.decode(),flags=re.S);head,body=text.split('<body>',1);f.write_text(head+'<body>'+readable(body));files[n]=f
c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=str(f)) for n,f in files.items()],commit_message='Improve numeric spacing in continuation report prose')
for n,f in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==f.read_bytes();p['files'][n]=hashlib.sha256(f.read_bytes()).hexdigest()
p.setdefault('initial_commit',p['commit']);p['commit']=c.oid;proof.write_text(json.dumps(p,indent=2)+'\n');print(c.oid)
