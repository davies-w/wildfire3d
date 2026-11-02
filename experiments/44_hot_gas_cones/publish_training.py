"""Publish only complete, validated TRAIN cone artifacts; preserve earlier pages."""
from pathlib import Path
import json,hashlib,requests,argparse
from huggingface_hub import HfApi,CommitOperationAdd,get_token
R=Path(__file__).resolve().parent;D=R/'data';proof=json.loads((D/'training-summary/validation.json').read_text());assert proof['passed'] and proof['training_histories']==1662 and proof['frames']==151242
api=HfApi();repo='wdavies/fire-state-storyboards';files=[]
for folder,dest in [(D/'training-histories','histories'),(D/'training-summary','summary'),(D/'training-report','')]:
 for p in sorted(folder.glob('*')):
  if p.is_file():files.append((p,'cones44/training/'+(dest+'/' if dest else '')+p.name))
parser=argparse.ArgumentParser();parser.add_argument('--report-only',action='store_true');args=parser.parse_args()
upload_files=[x for x in files if x[1]=='cones44/training/index.html'] if args.report_only else files
commits=[]
for start in range(0,len(upload_files),300):
 batch=upload_files[start:start+300];c=api.create_commit(repo_id=repo,repo_type='space',operations=[CommitOperationAdd(path_in_repo=dest,path_or_fileobj=str(p)) for p,dest in batch],commit_message=f'Preserve full training cone artifacts batch {start//300+1}');commits.append(c.oid);print('Published files',min(start+300,len(upload_files)),'/',len(upload_files),flush=True)
response=requests.get(f'https://huggingface.co/spaces/{repo}/resolve/main/cones44/index.html',headers={'Authorization':'Bearer '+get_token()},timeout=60);response.raise_for_status();old=response.content.decode('utf-8');link='<section><h2>All training data extracted</h2><p><a href="training/index.html">Inspect all1,662 rotation-0 training histories,151,242 saved frames, complete arrays and coverage validation.</a> No validation or test histories were included.</p></section>'
updated=old if 'training/index.html' in old else old.replace('</body>',link+'</body>') if '</body>' in old else old.replace('</html>',link+'</html>')
assert 'training/index.html' in updated
c=api.create_commit(repo_id=repo,repo_type='space',operations=[CommitOperationAdd(path_in_repo='cones44/index.html',path_or_fileobj=updated.encode())],commit_message='Link full training cone extraction from original comparison');commits.append(c.oid)
result=dict(repo=repo,commits=commits,url='https://wdavies-fire-state-storyboards.static.hf.space/cones44/training/index.html',files=[dict(path=dest,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p,dest in files],earlier_pages_preserved=True)
(R/'training-publication.json').write_text(json.dumps(result,indent=2)+'\n');print(result['url'])
