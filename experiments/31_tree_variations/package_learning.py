from pathlib import Path
import json,tarfile,hashlib,io
R=Path(__file__).parent
files={n:R/n for n in ['learning_worker.py','geometry_model.py','sequence.py','original_cnn.py','previous_loss.py','snapshot_evaluation.py','fresh-tests.json','data/geometries.npz','data/models/sequence_stage1.pt']};files['cases.json']=R/'development.json'
cs=json.loads((R/'development.json').read_text())
for c in cs:
 n='data/'+c['case']+'-material.npz';files[n]=R/n
 if c['new_geometry']:
  for suffix in ['.npy','-time.npy']:n='data/fields/'+c['case']+suffix;files[n]=R/n
hashes={}
with tarfile.open(R/'data/learning-overlay.tar','w') as tar:
 for n,p in files.items():
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  hashes[n]=h.hexdigest();tar.add(p,arcname=n)
 raw=json.dumps(hashes,indent=2).encode();ti=tarfile.TarInfo('learning-hashes.json');ti.size=len(raw);tar.addfile(ti,io.BytesIO(raw))
(R/'results/learning-input-freeze.json').write_text(json.dumps(hashes,indent=2));print('Learning archive bytes',(R/'data/learning-overlay.tar').stat().st_size)
