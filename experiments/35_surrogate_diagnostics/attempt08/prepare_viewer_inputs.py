"""Freeze final models before decoding additional cases. No training or model selection."""
from pathlib import Path
import json,subprocess,hashlib,shutil,sys,tarfile,struct
import numpy as np
R=Path(__file__).parent;S=R.parent/'attempt07';X=R.parent.parent/'32_tree_expansion';G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';prefix='gs://tmrw-wildfire-20261015-trial/diagnostics35/attempt07/'
sys.path.insert(0,str(S));from fields import read_slice
(R/'data/labels').mkdir(exist_ok=True)
report=R/'data/training-report.json'
if not report.exists():subprocess.run([G,'storage','cp',prefix+'report.json',str(report)],check=True)
a=json.loads(report.read_text());assert len(a['models'])==10
freeze={}
for m in a['models']:
 f=m['frame'];ep=m['epochs'];name=f'time-{f:03}-epoch-{ep:03}.pt';p=R/'data/models'/name
 if not p.exists():subprocess.run([G,'storage','cp',prefix+name,str(p)],check=True)
 freeze[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
(R/'results/model-freeze.json').write_text(json.dumps(dict(selection='Final checkpoints as prescribed in completed attempt07; no selection based on added cases or viewer.',files=freeze),indent=2))
cases=json.loads((X/'cases.json').read_text());fit={c['case'] for c in json.loads((S/'cases.json').read_text()) if c['split']=='train'}
for c in cases:c['fit_role']='training snapshot' if c['case'] in fit else ('additional seed of training configuration' if c['split']=='train' else ('previously examined test' if c['split']=='test' else 'validation'))
(R/'cases.json').write_text(json.dumps(cases,indent=2));geoms=np.load(X/'data/geometries.npz');old=np.load(S/'data/geometries.npz');assert all(np.array_equal(old[n],geoms[n]) for n in old.files);np.savez_compressed(R/'data/geometries.npz',**{c['case']:geoms[c['case']] for c in cases})
proofs=[]
for c in cases:
 n=c['case'];out=R/'data/labels'/(n+'.npz');proof=R/'data/labels'/(n+'.json')
 if (S/'data/labels'/(n+'.npz')).exists():
  shutil.copy2(S/'data/labels'/(n+'.npz'),out);shutil.copy2(S/'data/labels'/(n+'.json'),proof)
 elif not out.exists():
  pp=list((X/'data/cloud_archive').rglob(n+'.summary.json'));sp=next(p for p in pp if json.loads(p.read_text()).get('result',{}).get('full_horizon'));meta=json.loads(sp.read_text());raw=sp.with_name(n+'.tar.gz');h=hashlib.sha256(raw.read_bytes()).hexdigest();assert h==meta['raw_sha256'];temp=None;deckok=False
  with tarfile.open(raw) as tar:
   for member in tar:
    assert not member.name.startswith('/') and '..' not in Path(member.name).parts and not member.issym() and not member.islnk()
    if member.name.endswith('/'+n+'.fds'):deckok=hashlib.sha256(tar.extractfile(member).read()).hexdigest()==c['deck_sha256']
    if not member.name.endswith('.sf'):continue
    stream=tar.extractfile(member);size=struct.unpack('<i',stream.read(4))[0];name=stream.read(size).decode().strip()
    if name!='TEMPERATURE':continue
    p=R/'data/temp.sf'
    with tar.extractfile(member) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
    _,unit,bounds,t,temp=read_slice(p);p.unlink();ii=[np.arange(k)+1-bounds[2*j] for j,k in enumerate([48,32,32])];temp=temp[:,ii[0]][:,:,ii[1]][:,:,:,ii[2]];assert unit=='C'
  assert deckok and temp.shape==(91,48,32,32) and max(abs(t-np.arange(0,181,2)))<.2
  mask=temp>50;np.savez_compressed(out,packed=np.packbits(mask.reshape(91,-1),axis=1),time=t,positive=mask.sum((1,2,3)));proof.write_text(json.dumps(dict(case=n,raw_sha256=h,deck_sha256=c['deck_sha256'],labels_sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
 q=json.loads(proof.read_text());assert hashlib.sha256(out.read_bytes()).hexdigest()==q['labels_sha256'];proofs.append(q);print('READY',len(proofs),n,flush=True)
(R/'results/input-audit.json').write_text(json.dumps(dict(cases=proofs,count=len(cases),scope='All472newgeometryarchivedtrajectories:360fitprimary,24additionalTRAINseeds,40validation,48previouslyexaminedtest. Frozenfinalmodels; no fitting or modelselection. Olderlegacycasesoutsidegeometrydomainexcluded.'),indent=2))
