"""User-authorized report-only publication; preserve existing hub contents."""
from pathlib import Path
import hashlib,json
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((R/'results/model-training-collected.json').read_text())['passed']
 api=HfApi();repo='wdavies/fire-reports';revision=api.repo_info(repo_id=repo,repo_type='space').sha
 prior=Path(hf_hub_download(repo_id=repo,repo_type='space',filename='index.html',revision=revision)).read_text()
 prefix='density36-baseline';link='<section><h2>Denser simulation data: 2,080 histories</h2><p><a href="density36-baseline/index.html">Completed non-overlapping baseline — all four states, ten test folds</a></p></section>'
 assert '</main>' in prior
 hub=prior if 'density36-baseline/index.html' in prior else prior.replace('</main>',link+'</main>',1)
 ops=[CommitOperationAdd(path_in_repo='index.html',path_or_fileobj=hub.encode())];files=[]
 for name in ['index.html','values.json','scenario-audit.json','sources.json']:
  p=R/'data/published-report'/name;assert p.is_file() and p.stat().st_size<20_000_000
  ops.append(CommitOperationAdd(path_in_repo=prefix+'/'+name,path_or_fileobj=str(p)))
  files.append(dict(path=prefix+'/'+name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 commit=api.create_commit(repo_id=repo,repo_type='space',operations=ops,parent_commit=revision,commit_message='Publish verified density36 non-overlapping baseline report')
 for item in files:
  p=Path(hf_hub_download(repo_id=repo,repo_type='space',filename=item['path'],revision=commit.oid))
  assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 proof=dict(repo=repo,commit=commit.oid,previous_commit=revision,files=files,report_only=True,raw_data_published=False,url='https://wdavies-fire-reports.hf.space/'+prefix+'/index.html')
 (R/'results/report-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof['url'])
if __name__=='__main__':main()
