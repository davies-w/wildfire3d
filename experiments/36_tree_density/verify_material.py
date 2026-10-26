"""Stream immutable raw archives once, verify every byte, retain material inputs.
Full raw archives and restart files remain unchanged in private GCS. No simulation.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json,subprocess,tarfile,threading
from cloud import G
R=Path(__file__).resolve().parent
class HashStream:
 def __init__(self,src):self.src=src;self.digest=hashlib.sha256();self.size=0
 def read(self,n=-1):
  b=self.src.read(n);self.digest.update(b);self.size+=len(b);return b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int);args=ap.parse_args()
 root=R/'data/verified-material';root.mkdir(exist_ok=True)
 with (R/'data/material-verify.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  inventory=json.loads((R/'data/raw-inventory.json').read_text());count=0
  for row in inventory['archives']:
   n=row['case'];dest=root/n
   if (dest/'verified.json').exists():
    old=json.loads((dest/'verified.json').read_text());assert old['raw_sha256']==row['sha256']
    if any(x.endswith('.sf') for x in old['retained_material_inputs']):continue
   partial=root/(n+'.partial');assert not partial.exists(),f'Inspect preserved interrupted extraction before retry: {partial}'
   partial.mkdir();members={};retained=[]
   with (partial/'transport.log').open('wb') as log:
    proc=subprocess.Popen([G,'storage','cat',row['uri']],stdout=subprocess.PIPE,stderr=log)
    timer=threading.Timer(1800,proc.kill);timer.start();stream=HashStream(proc.stdout)
    try:
     with tarfile.open(fileobj=stream,mode='r|gz') as tar:
      for member in tar:
       if not member.isfile():continue
       name=Path(member.name).name;assert name not in members,member.name
       # Keep one slice solely for its actual output timestamps; nominal 2-s times
       # would change the established state sampling protocol.
       keep=name.endswith(('.prt5','.csv','.fds')) or (name.endswith('.sf') and not any(x.endswith('.sf') for x in retained))
       dst=(partial/name).open('wb') if keep and not (dest/name).exists() else None;sha=hashlib.sha256();size=0
       try:
        with tar.extractfile(member) as src:
         while b:=src.read(1024*1024):
          sha.update(b);size+=len(b)
          if dst:dst.write(b)
       finally:
        if dst:dst.close()
       assert size==member.size
       members[name]={'sha256':sha.hexdigest(),'bytes':size}
       if keep:retained.append(name)
     while stream.read(1024*1024):pass
     assert proc.wait(timeout=30)==0,'Archive transport failed; partial evidence retained'
     assert stream.size==row['bytes'] and stream.digest.hexdigest()==row['sha256'],'Raw archive checksum mismatch'
     sources=[R/'data/summaries'/f'{n}.json',R/'data/cloud-collected'/row['group']/f'{n}.json',R/'data/interrupted'/row['group']/f'{n}.json']
     summary=next(json.loads(p.read_text()) for p in sources if p.exists())
     assert all((partial/name).exists() or (dest/name).exists() for name in [f'{n}_1.prt5',f'{n}_devc.csv'])
     assert members[n+'.fds']['sha256']==summary['deck_sha256']
     for checkpoint in summary['checkpoint_manifest']['files']:
      assert members[checkpoint['name']]=={'sha256':checkpoint['sha256'],'bytes':checkpoint['bytes']}
     proof={'case':n,'raw_uri':row['uri'],'raw_sha256':row['sha256'],'raw_bytes':stream.size,'checkpoint_hashes_verified':True,'retained_material_inputs':retained,'members':members,'full_raw_retained_in_private_gcs':True,'no_training_or_simulation':True}
     (partial/'verified.json').write_text(json.dumps(proof,indent=2)+'\n')
     if dest.exists():
      assert old['members']==members,'Archive changed during timestamp backfill'
      (dest/'verified-before-timestamps.json').write_text(json.dumps(old,indent=2)+'\n')
      for p in list(partial.iterdir()):
       target=dest/('timestamp-transport.log' if p.name=='transport.log' else p.name)
       assert p.name=='verified.json' or not target.exists(),target
       p.replace(target)
      partial.rmdir()
     else:partial.rename(dest)
    finally:
     timer.cancel()
     if proc.poll() is None:proc.kill();proc.wait()
     proc.stdout.close()
   count+=1;print('VERIFIED_MATERIAL',n,stream.size,flush=True)
   if args.limit and count>=args.limit:break
if __name__=='__main__':main()
