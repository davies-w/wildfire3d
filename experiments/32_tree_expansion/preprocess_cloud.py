"""Decode one development case at a time in cloud; preserve raw objects remotely."""
import json,hashlib,tarfile,shutil,urllib.request,urllib.parse
from pathlib import Path
import numpy as np
from fields import extract
from material_reader import frames
R=Path(__file__).parent
BUCKET='tmrw-wildfire-20261015-trial'
def download(key,path):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(req,timeout=20))['access_token']
 url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(key,safe='')+'?alt=media'
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=300) as src,path.open('wb') as dst:shutil.copyfileobj(src,dst,8*1024**2)
def main():
 cs=json.loads((R/'cases.json').read_text());groups=json.loads((R/'groups.json').read_text());geoms=dict(np.load(R/'data/geometries.npz'));audits=[]
 for c in cs:
  if not c['case'].startswith('x32_'):continue
  assert c['split']!='test';n=c['case'];group=next(g['id'] for g in groups if n in g['cases']);prefix='expansion32/'+group+'/'+n
  p=R/'data'/('raw-'+n+'.tar.gz');summary=R/'data'/('raw-'+n+'.json');download(prefix+'.summary.json',summary);meta=json.loads(summary.read_text());assert meta['result']['full_horizon'] and meta['resume']['passed'];download(prefix+'.tar.gz',p)
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
  assert h.hexdigest()==meta['raw_sha256'];dest=R/'data/cloud';dest.mkdir(exist_ok=True)
  with tarfile.open(p) as tar:
   for member in tar.getmembers():assert not member.name.startswith('/') and '..' not in Path(member.name).parts and not member.issym() and not member.islnk()
   tar.extractall(dest)
  folder=dest/n;assert hashlib.sha256((folder/(n+'.fds')).read_bytes()).hexdigest()==c['deck_sha256']
  for rr in meta['checkpoint_manifest']['files']:assert hashlib.sha256((folder/rr['name']).read_bytes()).hexdigest()==rr['sha256']
  report=extract(c);times=[];mass=[];temp=[];actual=None
  for t,ps,labels in frames(folder/(n+'_1.prt5')):
   if not len(ps[0][0]):continue
   mm=np.zeros((4,12,8,8),np.float32);tt=np.zeros_like(mm);ag=np.zeros_like(geoms[n])
   for k,(x,q) in enumerate(ps[:4]):
    assert labels[k][:3]==['PARTICLE TEMPERATURE','PARTICLE MASS','PARTICLE WEIGHTING FACTOR']
    ix=(x/2).astype(int);m=q[:,1]*q[:,2];np.add.at(mm[k],tuple(ix.T),m);np.add.at(tt[k],tuple(ix.T),m*q[:,0]);ig=(x/.5).astype(int);np.add.at(ag[k],tuple(ig.T),m/.125)
   if actual is None:actual=ag
   times.append(t);mass.append(mm);temp.append(np.divide(tt,mm,out=np.full_like(tt,20),where=mm>0))
  err=float(abs(actual-geoms[n]).max());assert err<1e-4,(n,err);wanted=np.load(R/'data/fields'/(n+'-time.npy'));times=np.array(times);ids=abs(times[:,None]-wanted).argmin(0);assert max(abs(times[ids]-wanted))<.11
  np.savez_compressed(R/'data'/(n+'-material.npz'),mass=np.array(mass)[ids],temperature=np.array(temp)[ids],time=wanted)
  audits.append(dict(case=n,density_error=err,raw_sha256=h.hexdigest(),report=report));(R/'results/learning-data-audit.json').write_text(json.dumps(audits,indent=2));p.unlink();shutil.rmtree(folder)
  print('PREPROCESSED',n,flush=True)
if __name__=='__main__':main()
