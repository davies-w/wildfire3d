"""Cloud-only continuation of a hash-pinned FDS checkpoint; no origin probe or repeat."""
import json,time,signal,hashlib,tarfile,io,urllib.request,urllib.parse,re,traceback
from pathlib import Path
import pilot_worker06 as w
from transport import upload,token

def main():
 root=Path('/study');cfg=json.loads((root/'task.json').read_text());c=cfg['case'];name=c['pilot_case'];plan=json.loads((root/'recovery.json').read_text())[name]
 assert '_fine' not in name and w.sha(w.BINARY)==w.EXPECTED_BINARY
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/id',headers={'Metadata-Flavor':'Google'});assert urllib.request.urlopen(req,timeout=5).read().isdigit()
 source=(root/'decks'/f'{name}.fds').read_text();assert hashlib.sha256(source.encode()).hexdigest()==c['deck_sha256']
 evidence=root/'evidence';evidence.mkdir();folder=evidence/'solve';folder.mkdir();signal.signal(signal.SIGTERM,w.halt);signal.signal(signal.SIGINT,w.halt)
 class Parts(io.RawIOBase):
  def __init__(self):self.parts=iter(plan['archive_parts']);self.current=io.BytesIO()
  def readable(self):return True
  def readinto(self,buf):
   while True:
    n=self.current.readinto(buf)
    if n:return n
    try:p=next(self.parts)
    except StopIteration:return 0
    url='https://storage.googleapis.com/storage/v1/b/tmrw-wildfire-20261015-trial/o/'+urllib.parse.quote(p['name'],safe='')+'?alt=media&generation='+p['generation']
    b=urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token()}),timeout=180).read();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];self.current=io.BytesIO(b)
 stream=io.BufferedReader(Parts())
 with tarfile.open(fileobj=stream,mode='r|gz') as archive:
  for m in archive:
   parts=Path(m.name).parts;assert parts and parts[0]=='evidence' and '..' not in parts and not m.issym() and not m.islnk()
   if m.isfile():
    dest=folder/Path(*parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.extractfile(m).read())
 while stream.read(1024*1024):pass
 assert all((folder/x['name']).stat().st_size==x['bytes'] and w.sha(folder/x['name'])==x['sha256'] for x in plan['checkpoint_files'] if x['name']!='checkpoint.json')
 upload('restore.json',json.dumps(dict(passed=True,case=name,saved_step=plan['saved_step'],saved_time_s=plan['saved_time_s'],all_files_hash_verified=True)).encode())
 Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
 start=time.monotonic();deadline=start+14400;previous=(plan['saved_step'],plan['saved_time_s']);segments=[];success=False
 try:
  for index in range(40):
   assert time.monotonic()<deadline-930,'Continuation deadline reached; saved checkpoint retained'
   result=w.run(source.replace('&MISC ','&MISC RESTART=T, ',1),folder,300,name,hard_deadline=deadline);segments.append(result)
   log=(folder/result['log']).read_text();steps=re.findall(r'Time Step:\s+(\d+), Simulation Time:\s+([\d.Ee+-]+)\s+s',log);assert steps,'No new invocation progress'
   first=(int(steps[0][0]),float(steps[0][1]));assert first[0]>previous[0] and first[1]>previous[1], 'Restart repeated or failed to advance saved state'
   ds=w.devices(folder,name);text=(folder/(name+'.out')).read_text()
   success=result['returncode']==0 and not result['forced_termination'] and ds[-1]['Time']>=180-1e-5 and 'completed successfully' in (text+log).lower()
   w.save(evidence/'result.json',dict(passed=success,segments=segments,physical_time=ds[-1]['Time'],continued_from_step=plan['saved_step']))
   assert result['returncode']==0 and not result['forced_termination'],result
   if index==0:upload('startup.json',json.dumps(dict(passed=True,restored_step=plan['saved_step'],first_resumed_step=first[0],first_resumed_time_s=first[1],no_origin_probe=True)).encode())
   if success:break
   assert result['returncode']==0 and result['stopped'] and not result['forced_termination']
   previous=w.stopped_log_progress(folder/result['log'],previous)
   checkpoint=dict(index=index,deck_sha256=c['deck_sha256'],binary_sha256=w.EXPECTED_BINARY,step=previous[0],physical_time=previous[1],files=[dict(name=p.name,bytes=p.stat().st_size,sha256=w.sha(p)) for p in folder.iterdir() if p.is_file() and p.name!='checkpoint.json'])
   w.save(folder/'checkpoint.json',checkpoint);w.archive(folder,lambda n,b:upload(f'checkpoints/{index:03d}/'+n,b));upload(f'checkpoints/{index:03d}/verified.json',json.dumps(checkpoint).encode());assert not w.STOP,'Termination requested; checkpoint preserved'
  assert success,'Incomplete continuation; checkpoint retained'
 except BaseException:
  (evidence/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  manifest=w.archive(evidence,upload);upload('completion.json',json.dumps(dict(passed=success,case=name,archive=manifest,deck_sha256=c['deck_sha256'])).encode())
if __name__=='__main__':main()
