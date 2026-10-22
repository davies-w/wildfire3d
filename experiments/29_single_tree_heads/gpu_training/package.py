from pathlib import Path
import tarfile,json,hashlib,time
R=Path(__file__).parent;P=R.parent
files={n:P/n for n in ['models.py','original_cnn.py','previous_loss.py','cases.json','data/models/previous.pt','data/models/bounded.pt','data/models/strength.pt','results/temperature-bound.json','results/reuse.json','results/bounded-training.json','results/strength-training.json']}
files.update({'evaluate.py':R/'evaluate.py','cloud_worker.py':R/'cloud_worker.py'})
cs=json.loads((P/'cases.json').read_text());assert len(cs)==38
for c in cs:
 assert c['split'] in ['train','validation']
 for suffix in ['.npy','-time.npy']:n='data/fields/'+c['case']+suffix;files[n]=P/n
hashes={}
with tarfile.open(R/'data/inputs.tar','w',dereference=True) as tar:
 for n,p in files.items():
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  hashes[n]=h.hexdigest();tar.add(p,arcname=n)
 raw=json.dumps(hashes,indent=2).encode();import io
 ti=tarfile.TarInfo('input-hashes.json');ti.size=len(raw);tar.addfile(ti,io.BytesIO(raw))
(R/'results/input-hashes.json').write_text(json.dumps(hashes,indent=2))
print('Packaged',len(files),'files', (R/'data/inputs.tar').stat().st_size,flush=True)
