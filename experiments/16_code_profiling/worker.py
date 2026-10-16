"""Bounded sampling campaign; CPU usage comes from wait4, not FDS wall timers."""
import os,json,time,subprocess,signal,hashlib,tarfile,urllib.request,urllib.parse,csv,re,platform,glob
from pathlib import Path
ROOT=Path('/study');DATA=ROOT/'data';BINARY='/usr/local/bin/fds'

def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def upload(path,name):
    req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
    token=json.load(urllib.request.urlopen(req,timeout=10))['access_token']
    url='https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote('profile16/'+name,safe='')
    req=urllib.request.Request(url,data=path.read_bytes(),method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/gzip'})
    with urllib.request.urlopen(req,timeout=90) as r:print('UPLOADED',name,r.status,flush=True)
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
            if interrupted and time.monotonic()-stopped_at>30:
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
    archive=Path('/tmp')/(name+'.tar.gz')
    with tarfile.open(archive,'w:gz') as t:t.add(folder,arcname=name)
    if archive.stat().st_size>50*1024**2:raise RuntimeError('Per-case output exceeds 50 MiB')
    upload(archive,name+'.tar.gz');archive.unlink()
    print('RESULT',json.dumps(result),flush=True)
    return result

def main():
    DATA.mkdir(exist_ok=True);Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True);start=time.monotonic();cases=json.loads((ROOT/'manifest.json').read_text());results=[]
    save(DATA/'environment.json',dict(platform=platform.platform(),cpuinfo=Path('/proc/cpuinfo').read_text(),source_revision='ff928dbf68a2623ced3a007be75391c6dc6c9f90',threads=4))
    with tarfile.open('/tmp/profiling-binary.tar.gz','w:gz') as t:t.add(BINARY,arcname='fds')
    upload(Path('/tmp/profiling-binary.tar.gz'),'profiling-binary.tar.gz')
    for c in cases:
        remaining=6500-(time.monotonic()-start)-180
        if remaining<60:break
        limit=min(remaining,3600 if c['case']=='lot_full' else 900)
        result=run(c,limit);results.append(result)
        if result['returncode']!=0:raise RuntimeError('FDS failure: '+c['case'])
        if c['case']=='smoke':
            f=DATA/'smoke/profile-flat.txt'
            if not f.exists() or 'Total:' not in f.read_text():raise RuntimeError('Sampling self-test failed')
    save(DATA/'campaign.json',dict(results=results,total_wall_s=time.monotonic()-start,planned_cases=len(cases),completed_cases=len(results)))
    with tarfile.open('/tmp/summary.tar.gz','w:gz') as t:
        t.add(DATA/'campaign.json',arcname='campaign.json');t.add(DATA/'environment.json',arcname='environment.json')
    upload(Path('/tmp/summary.tar.gz'),'summary.tar.gz')
if __name__=='__main__':main()
