"""Cloud-only per-case runner. Produces immutable chunked archives through transport.py.
The caller must provide a unique prefix, verified input hashes and VM lifetime limits.
"""
from pathlib import Path
import os,json,time,hashlib,subprocess,signal,csv,re,tarfile,urllib.request,platform,traceback
ROOT=Path('/study');BINARY=Path('/usr/local/bin/fds');ACTIVE=None;STOP=False
EXPECTED_BINARY='70d829ede0c06ef0fe652c5878c1263e5ade8e6a0ec58f3c62f2169af592d692'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def halt(signum,frame):
 global STOP
 STOP=True
 if ACTIVE:(ACTIVE[1]/(ACTIVE[2]+'.stop')).touch()
def run(deck,folder,seconds,name):
 global ACTIVE
 folder.mkdir(parents=True,exist_ok=True);(folder/'input.fds').write_text(deck)
 env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
 start=time.monotonic();requested=None
 with (folder/f'run-{int(time.time_ns())}.log').open('w') as log:
  p=subprocess.Popen([str(BINARY),'input.fds'],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);ACTIVE=(p,folder,name)
  while p.poll() is None:
   if (STOP or time.monotonic()-start>seconds) and requested is None:(folder/(name+'.stop')).touch();requested=time.monotonic()
   if requested is not None and time.monotonic()-requested>90:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   time.sleep(.25)
 ACTIVE=None
 return dict(returncode=p.returncode,wall_seconds=time.monotonic()-start,stopped=requested is not None)
def devices(folder,name):
 with (folder/(name+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)];return [dict(zip(keys,map(float,row))) for row in r if row]
def archive(root,upload):
 # Bound memory with256MiB immutable chunks; the ordered manifest reconstructs tar.gz.
 class Sink:
  def __init__(self):self.buf=bytearray();self.parts=[];self.total=0
  def write(self,b):
   self.buf.extend(b);self.total+=len(b)
   while len(self.buf)>=256*1024**2:self.flush_part(256*1024**2)
   return len(b)
  def flush_part(self,n):
   b=bytes(self.buf[:n]);del self.buf[:n];name=f'archive-{len(self.parts):05d}.tar.gz.part';upload(name,b);self.parts.append(dict(name=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  def flush(self):pass
 sink=Sink()
 with tarfile.open(fileobj=sink,mode='w|gz') as t:t.add(root,arcname='evidence')
 if sink.buf:sink.flush_part(len(sink.buf))
 upload('archive-manifest.json',json.dumps(dict(parts=sink.parts,bytes=sink.total,complete=True)).encode())
def main():
 assert platform.system()=='Linux' and ROOT.is_dir(),'Cloud-only worker'
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/id',headers={'Metadata-Flavor':'Google'})
 instance=urllib.request.urlopen(req,timeout=3).read().decode();assert instance.isdigit()
 assert sha(BINARY)==EXPECTED_BINARY
 from transport import upload
 config=json.loads((ROOT/'task.json').read_text());c=config['case'];name=c['pilot_case'];deckpath=ROOT/'decks'/(name+'.fds');assert sha(deckpath)==c['deck_sha256']
 source=deckpath.read_text();root=ROOT/'evidence';root.mkdir();signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
 save(root/'input.json',config);(root/'original.fds').write_text(source);success=False
 try:
  probe=root/'probe';initial=source.replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01')
  a=run(initial,probe,600,name);assert a['returncode']==0 and not a['stopped']
  da=devices(probe,name);assert da[-1]['Time']>=.1-1e-6 and list(probe.glob('*.restart'))
  # Initial mass must match the independently calculated dry mass plus specified water.
  first=da[0];errors={k:abs(first[k+' mass']-v)/v for k,v in c['expected_wet_mass_kg'].items()};assert max(errors.values())<.01,errors
  (probe/'initial.out').write_bytes((probe/(name+'.out')).read_bytes())
  resumed=initial.replace('T_END=.1','T_END=.15').replace('&MISC ','&MISC RESTART=T, ',1)
  b=run(resumed,probe,600,name);assert b['returncode']==0 and not b['stopped'];db=devices(probe,name);assert db[-1]['Time']>=.15-1e-6
  firstout=(probe/'initial.out').read_text();lastout=(probe/(name+'.out')).read_text();assert 'restart' in lastout.lower()
  save(root/'startup.json',dict(passed=True,initial=a,resumed=b,mass_relative_error=errors,original_binary_sha256=EXPECTED_BINARY,scope='Cloud parse, initial mass and continuation to0.15s; probes are separate from full solve'))
  assert not STOP
  result=run(source,root/'solve',7200,name);ds=devices(root/'solve',name);out=(root/'solve'/(name+'.out')).read_text();success=result['returncode']==0 and not result['stopped'] and ds[-1]['Time']>=180-1e-5 and 'completed successfully' in out.lower()
  save(root/'result.json',dict(result,passed=success,physical_time=ds[-1]['Time'],instance_id=instance))
  assert success,'Incomplete solve; preserve and stop; never automatic retry'
 except BaseException:
  (root/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  files=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in root.rglob('*') if p.is_file()]
  save(root/'files.json',dict(files=files,passed=success));archive(root,upload)
if __name__=='__main__':main()
