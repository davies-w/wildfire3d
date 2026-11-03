"""Cloud-only fine-grid stop, upload/readback, restore and resume acceptance test."""
import json,time,os,platform,urllib.request,urllib.parse,hashlib,tarfile,shutil,re,signal,traceback
from pathlib import Path
import pilot_worker06 as worker
from transport import upload,object_metadata,token
ROOT=Path('/study');out=ROOT/'evidence';out.mkdir();started=time.monotonic()
config=json.loads((ROOT/'task.json').read_text());case=config['case'];name=case['pilot_case'];source=(ROOT/'decks'/f'{name}.fds').read_text()
assert platform.system()=='Linux' and worker.sha(worker.BINARY)==worker.EXPECTED_BINARY
r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/id',headers={'Metadata-Flavor':'Google'});assert urllib.request.urlopen(r,timeout=5).read().isdigit()
assert hashlib.sha256(source.encode()).hexdigest()==case['deck_sha256']
Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
signal.signal(signal.SIGTERM,worker.halt)
try:
 first=out/'first';a=worker.run(source,first,300,name,hard_deadline=started+1200)
 assert a['returncode']==0 and a['stopped'] and not a['forced_termination'],a
 pa=worker.stopped_log_progress(first/a['log']);restart=list(first.glob('*.restart'));assert restart and pa[1]>0
 hashes={p.name:worker.sha(p) for p in first.iterdir() if p.is_file()}
 manifest=worker.archive(first,lambda n,b:upload('snapshot/'+n,b));upload('first.json',json.dumps(dict(run=a,progress=pa,hashes=hashes)).encode())
 # Restore from pinned uploaded bytes, not a local directory copy.
 archive=out/'readback.tar.gz'
 with archive.open('wb') as f:
  for part in manifest['parts']:
   meta=object_metadata('snapshot/'+part['name']);url='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote(config['output_prefix']+'snapshot/'+part['name'],safe='')+'?alt=media&generation='+meta['generation']
   b=urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token()}),timeout=180).read();assert hashlib.sha256(b).hexdigest()==part['sha256'];f.write(b)
 restored=out/'restored';restored.mkdir()
 with tarfile.open(archive) as t:
  for m in t:
   p=Path(m.name);assert '..' not in p.parts and not p.is_absolute() and not m.issym() and not m.islnk()
   if m.isfile():dest=restored/Path(*p.parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(t.extractfile(m).read())
 assert all(worker.sha(restored/n)==h for n,h in hashes.items())
 # Keep the old output separate so progress must come from the resumed solve.
 (restored/(name+'.out')).rename(out/'first-output.txt')
 b=worker.run(source.replace('&MISC ','&MISC RESTART=T, ',1),restored,60,name,hard_deadline=started+2550)
 assert b['returncode']==0 and b['stopped'] and not b['forced_termination'],b
 pb=worker.stopped_log_progress(restored/b['log'],previous=pa)
 proof=dict(passed=True,case=name,first=a,resumed=b,first_progress=pa,resumed_progress=pb,cloud_upload_readback_restore=True,deck_sha256=case['deck_sha256'],wall_seconds=time.monotonic()-started)
 upload('proof.json',json.dumps(proof).encode());print(json.dumps(proof),flush=True)
except BaseException:
 for p in out.rglob('*'):
  if p.is_file() and p.suffix in {'.out','.log','.json','.fds','.csv'}:
   upload('diagnostic/'+p.relative_to(out).as_posix(),p.read_bytes())
 upload('failure.json',json.dumps(dict(passed=False,traceback=traceback.format_exc(),wall_seconds=time.monotonic()-started)).encode());raise
