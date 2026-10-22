"""Bounded sampling campaign; CPU usage comes from wait4, not FDS wall timers."""
import os,json,time,subprocess,signal,hashlib,tarfile,urllib.request,urllib.parse,csv,re,platform,glob
from pathlib import Path
ROOT=Path('/study');DATA=ROOT/'data';BINARY='/usr/local/bin/fds'

def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def upload(path,name):
    req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
    token=json.load(urllib.request.urlopen(req,timeout=10))['access_token']
    url='https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote('overnight21/c21_santa_rosa_east_03/'+name,safe='')
    req=urllib.request.Request(url,data=path.read_bytes(),method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/gzip'})
    with urllib.request.urlopen(req,timeout=600) as r:print('UPLOADED',name,r.status,flush=True)
def cpu_stat():
    p=Path('/sys/fs/cgroup/cpu.stat');return p.read_text() if p.exists() else ''
def run(c,limit):
    name=c['case'];folder=DATA/name;folder.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,OMP_NUM_THREADS='4',OMPI_ALLOW_RUN_AS_ROOT='1',OMPI_ALLOW_RUN_AS_ROOT_CONFIRM='1')
    if c['variant']=='passive':env.update(OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0')
    if c['profile']:env.update(LD_PRELOAD='/usr/lib/x86_64-linux-gnu/libprofiler.so.0',CPUPROFILE=str(folder/'cpu.prof'),CPUPROFILE_FREQUENCY='99')
    start=time.monotonic();stat_before=cpu_stat();interrupted=False;stopped_at=None
    with (folder/'run.log').open('w') as log:
        p=subprocess.Popen([BINARY,str(ROOT/'decks'/f'{name}.fds')],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        while True:
            pid,status,usage=os.wait4(p.pid,os.WNOHANG)
            if pid:break
            elapsed=time.monotonic()-start
            if elapsed>limit and not interrupted:
                # FDS stop-file permits normal profiler flush; incomplete horizon is explicitly marked.
                (folder/f'{name}.stop').touch();interrupted=True;stopped_at=time.monotonic()
            if interrupted and time.monotonic()-stopped_at>120:
                os.killpg(p.pid,signal.SIGTERM)
                time.sleep(2)
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                _,status,usage=os.wait4(p.pid,0);break
            time.sleep(.2)
    rc=os.waitstatus_to_exitcode(status);p.returncode=rc
    out=(folder/f'{name}.out').read_text(errors='replace') if (folder/f'{name}.out').exists() else ''
    rows=[];dev=folder/f'{name}_devc.csv'
    if dev.exists():
        with dev.open() as f:
            r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)]
            rows=[dict(zip(keys,map(float,v))) for v in r if v]
    last=rows[-1]['Time'] if rows else None
    result=dict(c,returncode=rc,wall_seconds=time.monotonic()-start,cpu_user_s=usage.ru_utime,cpu_system_s=usage.ru_stime,max_rss_kib=usage.ru_maxrss,voluntary_context_switches=usage.ru_nvcsw,involuntary_context_switches=usage.ru_nivcsw,stopped_by_budget=interrupted,physical_seconds_reached=last,full_horizon=bool(last is not None and last>=c['horizon_s']-1e-5 and rc==0 and not interrupted and 'completed successfully' in out.lower()),final_devices=rows[-1] if rows else {},cgroup_cpu_before=stat_before,cgroup_cpu_after=cpu_stat(),binary_sha256=hashlib.sha256(Path(BINARY).read_bytes()).hexdigest())
    if c['profile'] and (folder/'cpu.prof').exists():
        for label,flags in [('flat',['--text']),('cumulative',['--text','--cum']),('lines',['--text','--lines']),('callgraph',['--dot'])]:
            with (folder/f'profile-{label}.txt').open('w') as f:
                q=subprocess.run(['google-pprof',*flags,BINARY,str(folder/'cpu.prof')],stdout=f,stderr=subprocess.STDOUT,timeout=60)
            result['pprof_'+label+'_rc']=q.returncode
    save(folder/'result.json',result)
    (folder/(name+'.fds')).write_bytes((ROOT/'decks'/f'{name}.fds').read_bytes())
    save(folder/'checkpoint-manifest.json', {'files': [{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.glob('*.restart')], 'binary_sha256':result['binary_sha256'], 'resume_requires':'same Linux binary, all result files and RESTART=T; no automatic resubmission'})
    archive=Path('/tmp')/(name+'.tar.gz')
    with tarfile.open(archive,'w:gz') as t:t.add(folder,arcname=name)
    if archive.stat().st_size>2*1024**3:raise RuntimeError('Per-case output exceeds 50 MiB')
    upload(archive,name+'.tar.gz');archive.unlink()
    print('FINISHED',name,'complete=',result['full_horizon'],'wall_s=',round(result['wall_seconds'],1),flush=True)
    return result
