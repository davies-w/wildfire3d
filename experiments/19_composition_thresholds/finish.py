"""One-shot completion process; never creates or retries cloud compute."""
import datetime,json,subprocess,sys,time
from pathlib import Path
import cloud
ROOT=Path(__file__).resolve().parent
PY=sys.executable
def main():
    execution=json.loads((ROOT/'results/job-reservation.json').read_text())['execution'].split('/')[-1]
    started=time.monotonic()
    while True:
        status=cloud.gc('workflows','executions','describe',execution,'--workflow='+cloud.WORKFLOW,'--location=us-central1')
        if status['state']!='ACTIVE':break
        if time.monotonic()-started>21600:raise RuntimeError('Local wait limit; inspect independent cloud controller')
        time.sleep(60)
    cloud.status()
    assert all(not v for v in json.loads((ROOT/'results/cleanup.json').read_text()).values()),'Resources remain'
    parse=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
    elapsed=(parse(status['endTime'])-parse(status['startTime'])).total_seconds()
    (ROOT/'results/cost.json').write_text(json.dumps(dict(controller_elapsed_s=elapsed,
        compute_estimate_usd=elapsed/3600*.065744,including_ancillary_allowance_usd=elapsed/3600*.065744+.1,
        invoice_confirmed=False),indent=2)+'\n')
    def run(*args):subprocess.run([PY,*args],cwd=ROOT,check=True)
    run('fetch.py');run('evidence.py','bundle')
    dvc=Path(PY).with_name('dvc')
    subprocess.run([str(dvc),'add','data/cloud-evidence.tar.gz'],cwd=ROOT,check=True)
    status=json.loads((ROOT/'data/cloud/completion-status.json').read_text())
    if status['status']!='complete':raise RuntimeError('Campaign coverage/execution gate: '+str(status.get('error')))
    for stage in ('restore_reuse','restore_cloud','development','train','predict','test','evaluate'):
        subprocess.run([str(dvc),'repro',stage],cwd=ROOT,check=True)
    (ROOT/'results/completion.json').write_text(json.dumps(dict(status='complete',finished_unix=time.time()),indent=2)+'\n')
    print('Complete: results/findings.md',flush=True)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        (ROOT/'results/completion.json').write_text(json.dumps(dict(status='needs_attention',error=repr(exc),time=time.time()),indent=2)+'\n')
        raise
