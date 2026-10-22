"""One-shot local completion worker for the already authorized cloud execution.

Never launches/retries cloud compute. Cloud cleanup operates independently of
this process and of laptop availability. Resuming this script is safe.
"""
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path
import cloud
ROOT=Path(__file__).resolve().parent
PY=sys.executable

def run(*args):
    subprocess.run([PY,*args],cwd=ROOT,check=True)

def main():
    execution=json.loads((ROOT/'results/job-reservation.json').read_text())['execution'].split('/')[-1]
    started=time.monotonic()
    while True:
        status=cloud.gc('workflows','executions','describe',execution,'--workflow='+cloud.WORKFLOW,'--location=us-central1')
        if status['state']!='ACTIVE':break
        if time.monotonic()-started>21600:raise RuntimeError('Local wait limit reached; inspect independent cloud controller')
        time.sleep(60)
    cloud.status()
    inv=json.loads((ROOT/'results/cleanup.json').read_text())
    assert all(not objects for objects in inv.values()),'Residual cloud resources need attention'
    parse=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
    elapsed=(parse(status['endTime'])-parse(status['startTime'])).total_seconds()
    cost=dict(controller_elapsed_s=elapsed,compute_estimate_usd=elapsed/3600*.065744,
              including_ancillary_allowance_usd=elapsed/3600*.065744+.1,invoice_confirmed=False)
    (ROOT/'results/cost.json').write_text(json.dumps(cost,indent=2)+'\n')
    run('fetch.py');run('evidence.py','bundle')
    # External cloud output is a pipeline input; restored data is a stage output.
    dvc=Path(PY).with_name('dvc')
    subprocess.run([str(dvc),'add','data/cloud-evidence.tar.gz'],cwd=ROOT,check=True)
    campaign=json.loads((ROOT/'data/cloud/campaign.json').read_text())
    if campaign['status']!='complete' or len(campaign['results'])!=48:
        raise RuntimeError('Incomplete solver campaign; '+str(campaign.get('error')))
    for stage in ('restore_cloud','development','train','test','evaluate'):
        subprocess.run([str(dvc),'repro',stage],cwd=ROOT,check=True)
    (ROOT/'results/completion.json').write_text(json.dumps(dict(status='complete',finished_unix=time.time()),indent=2)+'\n')
    print('Pilot complete: results/findings.md',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        (ROOT/'results/completion.json').write_text(json.dumps(dict(status='needs_attention',error=repr(exc),time=time.time()),indent=2)+'\n')
        raise
