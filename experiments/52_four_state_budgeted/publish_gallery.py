"""Publish the explicitly approved test gallery and an additive homepage card."""
from pathlib import Path
import sys,json,hashlib,yaml
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
R=Path(__file__).resolve().parent;ROOT=R.parents[1];D=R/'data/test-gallery';sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
assert json.loads((R/'gallery-verification.json').read_text())['passed']
assert not (R/'gallery-publication.json').exists(),'Inspect prior publication before retrying'
hf.STATE=R/'private/hf-gallery';hf.plan_records([str(R/'dvc.yaml')+':build_gallery']);hf.upload(hf.STATE/'plan.json')
lock=yaml.safe_load((R/'dvc.lock').read_text());outs=lock['stages']['build_gallery']['outs'];ptr=hf.STATE/'restoration-source.dvc';ptr.write_text(yaml.safe_dump({'outs':[{**o,'path':'../../'+o['path']} for o in outs]},sort_keys=False));hf.restore_records([str(ptr)],R/'private/gallery-roundtrip')
api=HfApi();repo='wdavies/fire-reports';parent=R/'private/site-parent';rev=json.loads((parent/'revision.json').read_text())['revision'];assert api.repo_info(repo,repo_type='space').sha==rev
old=(parent/'index.html').read_text();assert Path(hf_hub_download(repo,'index.html',repo_type='space',revision=rev)).read_text()==old
card='<a class="card" href="fourstate52/index.html" target="_blank" rel="noopener noreferrer"><span class="tag">Experiment 52 · test gallery</span><h2>Four-state predictions →</h2><p>225 held-out scenarios · selected epoch 166. Four charts per row with configuration icons, simulation/model overlays and a constant-state baseline. Fresh eight-history GRU; one grouped rotation.</p></a>'
assert '<div class="cards">' in old and 'fourstate52/index.html' not in old
new=old.replace('<div class="cards">','<div class="cards">'+card,1);assert new.replace(card,'',1)==old
files={f'fourstate52/{p.name}':p.read_bytes() for p in D.iterdir() if p.is_file()};assert len(files)==76
existing=set(api.list_repo_files(repo,repo_type='space',revision=rev));assert not existing&set(files)
files['index.html']=new.encode();c=api.create_commit(repo_id=repo,repo_type='space',parent_commit=rev,operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=b) for n,b in files.items()],commit_message='Publish experiment52 test gallery and homepage card')
(R/'private/gallery-commit.json').write_text(json.dumps({'commit':c.oid}))
for n,b in files.items():assert Path(hf_hub_download(repo,n,repo_type='space',revision=c.oid)).read_bytes()==b
proof=dict(passed=True,commit=c.oid,parent_revision=rev,HF_independent_restoration=True,public_readback_exact=True,prior_homepage_preserved=True,files={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},url='https://wdavies-fire-reports.hf.space/fourstate52/index.html',homepage='https://wdavies-fire-reports.hf.space/');(R/'gallery-publication.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof['url'])
