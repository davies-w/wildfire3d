"""SHA-verified local temperature decoding and classification labels; NO optimization."""
from pathlib import Path
import json,hashlib,tarfile,struct,shutil
import numpy as np
from fields import read_slice
R=Path(__file__).parent;source=R.parent.parent/'33_representation_loss/attempt14';archive=R.parent.parent/'32_tree_expansion/data/cloud_archive'
cases=json.loads((R/'cases.json').read_text());plan=json.loads((R/'coverage-plan.json').read_text());out=R/'data/labels';out.mkdir(exist_ok=True)
freeze=json.loads((source/'results/input-freeze.json').read_text());geom=source/'data/geometries.npz';assert hashlib.sha256(geom.read_bytes()).hexdigest()==freeze['data/geometries.npz'];shutil.copy(geom,R/'data/geometries.npz')
train={c['configuration'] for c in cases if c['split']=='train'};val={c['configuration'] for c in cases if c['split']=='validation'};assert len(cases)==400 and len(train)==360 and len(val)==32 and not train&val;assert train==set(plan['train_configurations']) and val==set(plan['validation_configurations'])
audit=[];positive=np.zeros(91,np.int64);nc=0
for c in cases:
 n=c['case'];dest=out/(n+'.npz');proof=out/(n+'.json')
 if not dest.exists() or not proof.exists():
  paths=list(archive.rglob(n+'.summary.json'));candidates=[]
  for sp in paths:
   meta=json.loads(sp.read_text())
   if meta.get('result',{}).get('full_horizon'):candidates.append((sp,meta))
  assert candidates,n
  sp,meta=candidates[0];raw=sp.with_name(n+'.tar.gz');h=hashlib.sha256()
  with raw.open('rb') as f:
   for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
  assert h.hexdigest()==meta['raw_sha256'],n
  a=None;times=None;deckok=False
  with tarfile.open(raw) as tar:
   for m in tar:
    assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
    if m.name.endswith('/'+n+'.fds'):deckok=hashlib.sha256(tar.extractfile(m).read()).hexdigest()==c['deck_sha256']
    if not m.name.endswith('.sf'):continue
    f=tar.extractfile(m);size=struct.unpack('<i',f.read(4))[0];name=f.read(size).decode().strip()
    if name!='TEMPERATURE':continue
    temp=R/'data/temperature.sf'
    with tar.extractfile(m) as src,temp.open('wb') as dst:shutil.copyfileobj(src,dst)
    name,unit,bounds,t,a=read_slice(temp);temp.unlink();assert unit=='C'
    ii=[np.arange(z)+1-bounds[2*k] for k,z in enumerate([48,32,32])];a=a[:,ii[0]][:,:,ii[1]][:,:,:,ii[2]];times=t
  assert deckok and a is not None and a.shape==(91,48,32,32) and np.isfinite(a).all()
  nominal=np.arange(0,181,2);assert np.max(abs(times-nominal))<=.2,(n,float(np.max(abs(times-nominal))))
  masks=a>50;packed=np.packbits(masks.reshape(91,-1),axis=1);np.savez_compressed(dest,packed=packed,time=times,positive=masks.sum((1,2,3)))
  proof.write_text(json.dumps(dict(case=n,raw_sha256=h.hexdigest(),deck_sha256=c['deck_sha256'],labels_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),max_time_jitter_s=float(np.max(abs(times-nominal))))))
 z=np.load(dest);q=json.loads(proof.read_text());assert hashlib.sha256(dest.read_bytes()).hexdigest()==q['labels_sha256'];audit.append(q)
 if c['split']=='train':positive+=z['positive'];nc+=1
 print('LABELS',len(audit),n,flush=True)
assert nc==360
cells=48*32*32;pop=dict(positive=positive.tolist(),negative=(nc*cells-positive).tolist(),training_snapshots_per_epoch=nc*91,scope='TRAIN only, fixed population weights independently at each nominaltime')
(R/'data/class-population.json').write_text(json.dumps(pop,indent=2));(R/'results/labels-audit.json').write_text(json.dumps(dict(cases=audit,train_configurations=360,validation_configurations=32,validation_trajectories=40,hot_fraction_per_time=(positive/(nc*cells)).tolist()),indent=2))
