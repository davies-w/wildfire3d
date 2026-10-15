"""Admission guard. Requires deployed workflow and verified image, never raw job input.

The local ledger is a conservative reservation ledger, NOT Google's invoice.
Owner-level manual API calls can bypass this launcher; this is not an account cap.
"""
import argparse,fcntl,json,subprocess,time
from pathlib import Path
from study import ROOT,save
from test_controls import validate

GCLOUD='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud'
PROJECT='tmrw-wildfire-20261015'

def gc(*args):
    p=subprocess.run([GCLOUD,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout or '{}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['science','science-recovery','timeout','watchdog']);args=ap.parse_args()
    cfg=json.loads((ROOT/'controls.json').read_text())
    deployment=json.loads((ROOT/'results/cloud-deployment.json').read_text())
    if not deployment.get('verified'):raise RuntimeError('Cloud controls not verified/deployed')
    j=json.loads((ROOT/f'job-{args.mode}.json').read_text());validate(j)
    if j['taskGroups'][0]['taskSpec']['runnables'][0]['container']['imageUri']!=deployment['image']:raise RuntimeError('Image mismatch')
    ledger_path=ROOT/'results/cost-reservations.json'
    with (ROOT/'data/launch.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger=json.loads(ledger_path.read_text())
        if args.mode in [r['mode'] for r in ledger['jobs']]:raise RuntimeError('Trial already reserved; no automatic retry')
        if len(ledger['jobs'])>=4:raise RuntimeError('Four-job trial allowance exhausted')
        reservation=.025
        if ledger['reserved_usd']+reservation>cfg['admission_ceiling_usd']:raise RuntimeError('Cost allowance exhausted')
        for mode in ['science','science-recovery','timeout','watchdog']:
            executions=gc('workflows','executions','list','fds-'+mode,'--location=us-central1','--filter=state=ACTIVE')
            if executions:raise RuntimeError('Another experiment execution is active')
        jobs=gc('batch','jobs','list','--location=us-central1')
        if any(x['name'].endswith('/fds-controlled-trial') for x in jobs):raise RuntimeError('Prior job not removed')
        workers=gc('compute','instances','list','--filter=labels.trial_id=study15')
        if workers:raise RuntimeError('Prior workers remain')
        # Reserve before submission; ambiguous submission errors do not refund/retry.
        entry={'mode':args.mode,'reserved_usd':reservation,'submitted_unix':time.time(),'state':'reserved'}
        ledger['jobs'].append(entry);ledger['reserved_usd']+=reservation;save(ledger_path,ledger)
        result=gc('workflows','execute','fds-'+args.mode,'--location=us-central1')
        entry.update(state='submitted',execution=result['name']);save(ledger_path,ledger)
        print(json.dumps(result,indent=2))

if __name__=='__main__':main()
