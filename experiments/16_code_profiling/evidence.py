"""Snapshot completed cloud downloads or restore them locally; never starts compute."""
import argparse,hashlib,json,tarfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ARCHIVE=ROOT/'data/cloud-evidence.tar.gz'
def pack():
 files=sorted((ROOT/'data/downloads').glob('*.tar.gz'))
 if not files:raise RuntimeError('Fetch completed cloud evidence first')
 temporary=ARCHIVE.with_suffix('.tmp')
 with tarfile.open(temporary,'w:gz') as out:
  for p in files:out.add(p,arcname=p.name)
 temporary.replace(ARCHIVE)
 (ROOT/'results/evidence-manifest.json').write_text(json.dumps([{'url':'gs://tmrw-wildfire-20261015-trial/profile16/'+p.name,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'normalization':json.loads((ROOT/'results'/('archive-cleanup-'+p.name+'.json')).read_text()) if (ROOT/'results'/('archive-cleanup-'+p.name+'.json')).exists() else None} for p in files],indent=2)+'\n')
 # This bundle is an external cloud-compute input, not a local pipeline output.
 digest=hashlib.md5(ARCHIVE.read_bytes()).hexdigest()
 (ROOT/'cloud-evidence.dvc').write_text(f'outs:\n- md5: {digest}\n  size: {ARCHIVE.stat().st_size}\n  hash: md5\n  path: data/cloud-evidence.tar.gz\n')
def extract():
 downloads=ROOT/'data/restored-downloads'
 if downloads.exists():shutil.rmtree(downloads)
 downloads.mkdir(parents=True,exist_ok=True)
 with tarfile.open(ARCHIVE) as archive:archive.extractall(downloads,filter='data')
 for p in sorted(downloads.glob('*.tar.gz')):
  out=ROOT/('data/binary' if p.name=='profiling-binary.tar.gz' else 'data/cloud')
  out.mkdir(parents=True,exist_ok=True)
  with tarfile.open(p) as archive:archive.extractall(out,filter='data')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['pack','extract']);a=ap.parse_args()
 {'pack':pack,'extract':extract}[a.action]()
