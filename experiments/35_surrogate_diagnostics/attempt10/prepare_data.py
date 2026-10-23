"""Decode and verify archived inputs locally. No optimizer or model fitting."""
from pathlib import Path
import json,hashlib,tarfile,shutil
import numpy as np
from fields import extract
R=Path(__file__).parent;source=R.parent/'attempt05';archive=R.parent.parent/'32_tree_expansion/data/cloud_archive'
cases=json.loads((source/'cases.json').read_text());assert len(cases)==48
assert sum(c['split']=='train' for c in cases)==8 and sum(c['split']=='validation' for c in cases)==40
assert not ({c['configuration'] for c in cases if c['split']=='train'} & {c['configuration'] for c in cases if c['split']=='validation'})
manifest=json.loads((source/'restore-manifest.json').read_text());rows=[]
(R/'data/cloud').mkdir(parents=True,exist_ok=True)
for c in cases:
 n=c['case'];item=next(i for i in manifest if i['target'].endswith('/'+n+'.tar.gz'));p=archive/item['archive_relative'];assert p.stat().st_size==item['bytes'];assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==item['sha256']
 with tarfile.open(p) as tar:
  for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
  tar.extractall(R/'data/cloud')
 folder=R/'data/cloud'/n;assert hashlib.sha256((folder/(n+'.fds')).read_bytes()).hexdigest()==c['deck_sha256'];extract(c)
 a=np.load(R/'data/fields'/(n+'.npy'),mmap_mode='r');t=np.load(R/'data/fields'/(n+'-time.npy'));assert a.shape==(91,6,48,32,32) and len(t)==91 and np.all(np.diff(t)>0)
 rows.append(dict(case=n,archive_sha256=item['sha256'],array_sha256=hashlib.file_digest((R/'data/fields'/(n+'.npy')).open('rb'),'sha256').hexdigest(),time_min=float(t[0]),time_max=float(t[-1])))
 shutil.rmtree(folder);print('DECODED',n,flush=True)
geoms=np.load(R.parent/'attempt07/data/geometries.npz');np.savez_compressed(R/'data/geometries.npz',**{c['case']:geoms[c['case']] for c in cases})
(R/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
sc=json.loads((R.parent/'attempt03/data/collected/scales.json').read_text());(R/'scales.json').write_text(json.dumps(dict(encoded_std=sc['encoded_std'],source='attempt03 frozen TRAIN8 scales; no validation fitting'),indent=2)+'\n')
(R/'results/data-verification.json').write_text(json.dumps(dict(passed=True,rows=rows,train_cases=8,validation_cases=40,validation_configurations=32,shape=[91,6,48,32,32],scope='Previously examined development only. SHA verified original archives; all physical cell centers retained.'),indent=2)+'\n')
