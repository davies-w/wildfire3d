"""Verify complete published file inventory and read back representative artifacts."""
from pathlib import Path
import hashlib,json,time
import requests
from huggingface_hub import HfApi
R=Path(__file__).resolve().parent
p=R/'training-publication.json';receipt=json.loads(p.read_text());revision=receipt['commits'][-1]
remote=set(HfApi().list_repo_files(receipt['repo'],repo_type='space',revision=revision))
assert all(x['path'] in remote for x in receipt['files'])
histories=[x['path'] for x in receipt['files'] if '/histories/' in x['path']]
selected=['cones44/training/index.html','cones44/training/summary/targets.npz','cones44/training/summary/validation.json',histories[0],histories[-1]]
expected={x['path']:x['sha256'] for x in receipt['files']}
for name in selected:
    response=requests.get(f"https://huggingface.co/spaces/{receipt['repo']}/resolve/{revision}/{name}",timeout=90);response.raise_for_status()
    assert hashlib.sha256(response.content).hexdigest()==expected[name],name
body=(R/'data/training-report/index.html').read_bytes()
for attempt in range(12):
    response=requests.get(receipt['url'],timeout=30)
    if response.ok and body in response.content:break
    time.sleep(5)
else:raise AssertionError('Live report has not reached the verified published bytes')
parent=requests.get(receipt['url'].replace('training/index.html','index.html'),timeout=30);parent.raise_for_status();assert b'training/index.html' in parent.content
receipt['verification']=dict(passed=True,all_published_files_present=len(receipt['files']),readback_sha256_verified=selected,live_report_bytes_verified=True,parent_link_verified=True)
p.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt['verification'],indent=2))
