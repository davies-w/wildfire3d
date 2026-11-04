"""Cloud-only FDS runner: startup proof, bounded solve, remote stopped-state snapshots."""
from pathlib import Path
from completion_check03 import terminal_success
import os,json,time,hashlib,subprocess,signal,csv,re,tarfile,urllib.request,platform,traceback,shutil
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
def run(deck,folder,seconds,name,grace_seconds=900,hard_deadline=None,checkpoint_control=None):
 global ACTIVE
 folder.mkdir(parents=True,exist_ok=True);(folder/(name+'.stop')).unlink(missing_ok=True);(folder/'input.fds').write_text(deck)
 env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
 start=time.monotonic();requested=None;forced=False
 if hard_deadline is None:hard_deadline=start+seconds+grace_seconds+15
 assert grace_seconds>0 and hard_deadline>start
 logpath=folder/f'run-{time.time_ns()}.log'
 with logpath.open('w') as log:
  p=subprocess.Popen([str(BINARY),'input.fds'],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);ACTIVE=(p,folder,name)
  while p.poll() is None:
   if checkpoint_control is not None and requested is None:
    seconds=min(seconds,checkpoint_control.interval())
   if (STOP or time.monotonic()-start>seconds or time.monotonic()>=hard_deadline-grace_seconds-15) and requested is None:
    (folder/(name+'.stop')).touch();requested=time.monotonic()
    save(folder/'stop-request.json',dict(requested_wall_s=requested-start,checkpoint_interval_seconds=seconds,grace_seconds=grace_seconds,hard_deadline_remaining_s=hard_deadline-requested))
   if requested is not None and (time.monotonic()-requested>grace_seconds or time.monotonic()>=hard_deadline-10):
    forced=True
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   time.sleep(.25)
 ACTIVE=None
 return dict(returncode=p.returncode,wall_seconds=time.monotonic()-start,stopped=requested is not None,forced_termination=forced,stop_wait_seconds=None if requested is None else time.monotonic()-requested,log=logpath.name)
def stopped_log_progress(logpath,previous=None):
 """Read only this invocation's captured stdout, never an inherited .out file."""
 text=Path(logpath).read_text()
 pairs=list(re.finditer(r'Time Step:\s+(\d+), Simulation Time:\s+([\d.Ee+-]+)\s+s',text))
 assert pairs,'No simulation progress in invocation log'
 values=[(int(m[1]),float(m[2])) for m in pairs]
 assert all(b[0]>a[0] and b[1]>a[1] for a,b in zip(values,values[1:])), 'Non-increasing invocation progress'
 assert 'STOP: FDS stopped by user' in text[pairs[-1].end():], 'No clean-stop marker after progress'
 if previous is not None:
  assert values[0][0]>previous[0] and values[0][1]>previous[1], 'Resumed log contains old or non-advancing progress'
 return values[-1]
def devices(folder,name):
 with (folder/(name+'_devc.csv')).open() as f:
  r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)];return [dict(zip(keys,map(float,row))) for row in r if row]
def mass_row(rows):
 first=next(row for row in rows if row['Time']>0)
 assert first['Time']<=.100001,'Initial mass must be checked by 0.1s'
 return first
def archive(root,upload):
 class Sink:
  def __init__(self):self.buf=bytearray();self.parts=[];self.total=0
  def write(self,b):
   self.buf.extend(b);self.total+=len(b)
   while len(self.buf)>=64*1024**2:self.flush_part(64*1024**2)
   return len(b)
  def flush_part(self,n):
   b=bytes(self.buf[:n]);del self.buf[:n];name=f'archive-{len(self.parts):05d}.tar.gz.part';upload(name,b);self.parts.append(dict(name=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  def flush(self):pass
 sink=Sink()
 with tarfile.open(fileobj=sink,mode='w|gz') as t:t.add(root,arcname='evidence')
 if sink.buf:sink.flush_part(len(sink.buf))
 manifest=dict(parts=sink.parts,bytes=sink.total,complete=True)
 upload('archive-manifest.json',json.dumps(manifest).encode());return manifest

def main():
 assert platform.system()=='Linux' and ROOT.is_dir(),'Cloud-only worker'
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/id',headers={'Metadata-Flavor':'Google'})
 instance=urllib.request.urlopen(req,timeout=3).read().decode();assert instance.isdigit();assert sha(BINARY)==EXPECTED_BINARY
 from transport import upload,object_metadata,matches
 config=json.loads((ROOT/'task.json').read_text());c=config['case'];name=c['pilot_case'];deckpath=ROOT/'decks'/(name+'.fds');assert sha(deckpath)==c['deck_sha256']
 probe_bytes=b'tree48-immutable-transport';upload('transport.bin',probe_bytes);assert matches(object_metadata('transport.bin'),probe_bytes);upload('transport.bin',probe_bytes)
 source=deckpath.read_text();root=ROOT/'evidence';root.mkdir();signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
 Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
 save(root/'input.json',config);(root/'original.fds').write_text(source);success=False;start=time.monotonic()
 try:
  from checkpoint_control import CheckpointControl
  control=CheckpointControl();control.preflight()
  probe=root/'probe';initial=source.replace('T_END=180','T_END=.1').replace('DT_RESTART=30.','DT_RESTART=.05').replace('DT_DEVC=1.','DT_DEVC=.01')
  a=run(initial,probe,600,name);assert a['returncode']==0 and not a['stopped'],a
  da=devices(probe,name);assert da[-1]['Time']>=.1-1e-6 and list(probe.glob('*.restart'))
  first=mass_row(da);errors={k:abs(first[k+' mass']-v)/v for k,v in c['expected_wet_mass_kg'].items()};assert max(errors.values())<.01,errors
  # Resume from a separate copy, proving that state is portable across worker folders.
  restored=root/'restored-probe';shutil.copytree(probe,restored)
  resumed=initial.replace('T_END=.1','T_END=.15').replace('&MISC ','&MISC RESTART=T, ',1)
  b=run(resumed,restored,600,name);assert b['returncode']==0 and not b['stopped'];db=devices(restored,name);assert db[-1]['Time']>=.15-1e-6
  pattern=r'Time Step:\s+(\d+), Simulation Time:\s+([\d.]+)'
  steps1=re.findall(pattern,(probe/a['log']).read_text());steps2=re.findall(pattern,(restored/b['log']).read_text())
  assert steps1 and steps2 and int(steps2[0][0])>int(steps1[-1][0]) and float(steps2[0][1])>float(steps1[-1][1]),(steps1,steps2)
  proof=dict(passed=True,initial=a,resumed=b,mass_relative_error=errors,mass_check_time_s=first['Time'],binary_sha256=EXPECTED_BINARY,portable_restart=True,deck_sha256=c['deck_sha256'])
  save(root/'startup.json',proof);upload('startup.json',json.dumps(proof).encode());assert not STOP
  folder=root/'solve';solve_start=time.monotonic();segments=[];deck=source
  for index in range(30):
   remaining=min(7200-(time.monotonic()-solve_start),8400-(time.monotonic()-start));assert remaining>0,'Wall limit reached; last remote checkpoint retained'
   result=run(deck,folder,min(480,max(0,remaining-915)),name,hard_deadline=solve_start+7200,checkpoint_control=control);segments.append(result);ds=devices(folder,name);out=(folder/(name+'.out')).read_text()
   success=terminal_success(result,ds[-1]['Time'],folder/result['log'])
   save(root/'result.json',dict(passed=success,segments=segments,physical_time=ds[-1]['Time'],instance_id=instance,wall_seconds=time.monotonic()-start))
   if success:break
   assert not result['forced_termination'] and result['returncode']==0 and result['stopped'] and 'FDS stopped by user' in out and list(folder.glob('*.restart')),'Unexpected solver failure'
   progress=stopped_log_progress(folder/result['log'])
   checkpoint=dict(index=index,step=progress[0],physical_time=progress[1],deck_sha256=c['deck_sha256'],binary_sha256=EXPECTED_BINARY,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file() and p.name!='checkpoint.json'])
   save(folder/'checkpoint.json',checkpoint)
   archive(folder,lambda n,data:upload(f'checkpoints/{index:03d}/'+n,data))
   upload(f'checkpoints/{index:03d}/verified.json',json.dumps(checkpoint).encode())
   assert not STOP,'Termination requested; checkpoint archived'
   deck=source.replace('&MISC ','&MISC RESTART=T, ',1)
  assert success,'Incomplete solve; last remote checkpoint retained; no automatic retry'
 except BaseException:
  (root/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  files=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in root.rglob('*') if p.is_file()]
  save(root/'files.json',dict(files=files,passed=success));manifest=archive(root,upload)
  upload('completion.json',json.dumps(dict(passed=success,case=name,archive=manifest,deck_sha256=c['deck_sha256'])).encode())
if __name__=='__main__':main()
