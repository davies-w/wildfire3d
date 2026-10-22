"""Download new per-case evidence only; never launches compute."""
from pathlib import Path
import subprocess,tarfile,re,hashlib,json
ROOT=Path(__file__).resolve().parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud'
dest=ROOT/'data/downloads';dest.mkdir(parents=True,exist_ok=True)
out=ROOT/'data/cloud';out.mkdir(exist_ok=True)
p=subprocess.run([G,'storage','ls','gs://tmrw-wildfire-20261015-trial/domain17/*.tar.gz'],capture_output=True,text=True)
if p.returncode:
 print(p.stderr);raise SystemExit(p.returncode)
for url in p.stdout.splitlines():
 name=url.rsplit('/',1)[-1]
 if not re.fullmatch(r'[a-zA-Z0-9_-]+\.tar\.gz',name):continue
 target=dest/name
 if target.exists():continue
 subprocess.run([G,'storage','cp',url,str(target)],check=True)
 # FDS can write a restart on a normal stop-file cutoff despite DT_RESTART.
 # Repository policy retains physical evidence, never restart checkpoints.
 original_sha=hashlib.sha256(target.read_bytes()).hexdigest()
 with tarfile.open(target) as source:
  removed=[m.name for m in source.getmembers() if m.name.endswith('.restart')]
  if removed:
   temporary=target.with_suffix('.clean')
   with tarfile.open(temporary,'w:gz') as clean:
    for member in source.getmembers():
     if member.name in removed:continue
     clean.addfile(member,source.extractfile(member) if member.isfile() else None)
 if removed:
  temporary.replace(target)
  record={'url':url,'original_cloud_sha256':original_sha,'removed_restart_members':removed,'retained_archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
  (ROOT/'results'/('archive-cleanup-'+name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
 with tarfile.open(target) as archive:
  archive.extractall(out if name!='profiling-binary.tar.gz' else ROOT/'data/binary',filter='data')
 print('Fetched',name,flush=True)
