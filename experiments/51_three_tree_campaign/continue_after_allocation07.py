"""Continue untouched cases after a terminal, actual-allocation reconciliation."""
import argparse, base64, json, math, re, subprocess, time
from datetime import datetime
import requests, yaml
from cloud07 import B,BUCKET,G,P,PREFIX,PROJECT,R,WF,fcntl,gc,save,sha

def read(n):return json.loads((P/n).read_text())
def empty():
    for a in [('batch','jobs','list','--location=us-central1'),('compute','instances','list'),('compute','disks','list')]:assert not gc(*a,'--filter=name~t51r07')
def api():
    h={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip(),'Content-Type':'application/json'}
    return h,'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'
def get(h,url,n):return requests.get(url+requests.utils.quote(PREFIX+n,safe=''),headers=h,timeout=60)
def guards():
    assert not (P/'resume7-submission-intent.json').exists()
    a=read('november-terminal-audit.json');assert a['passed'] and a['cursor']==1483
    pairs=read('november-terminal-pairs.json');inds=[int(re.search(r't51r07-c(\d+)-',s)[1]) for s in pairs]
    assert len(inds)==len(set(inds)) and set(inds)==set(range(586,1483))-{681}
    assert all(x['insert'] and x['delete'] for x in pairs.values())
    empty()
    progress=read('progress-summary.json');assert progress['verified_complete']==1855 and progress['scientifically_collected']==1855
    covered=set()
    for selection in P.glob('collection-group*.json'):
        group=selection.stem.split('-')[-1];receipt=read('preservation-'+group+'.json')
        assert receipt['passed'] and receipt['remote_size_and_xet_verified'] and receipt['directory_anonymous_readback']
        assert receipt['plan_sha256']==sha(P/('scientific-plan-'+group+'.json'))
        ids=set(json.loads(selection.read_text())['indices']);assert not covered.intersection(ids);covered.update(ids)
    assert len(covered)+468==1855
    assert set(range(1483,1531)).isdisjoint(covered)
    assert time.time()<datetime.fromisoformat('2026-11-08T13:46:41+00:00').timestamp()
    subprocess.run([__import__('sys').executable,str(R/'monitor_billing07.py')],check=True)
    billing=read('nov06-monitor-reconciled.json');assert billing['within_ceiling']
    # Keep the original cap and all six unresolved admission reservations.
    state=dict(a['state']);held=[9,15,276,514,515,681]
    state['spent']=math.ceil(a['compute_upper_usd']*1e6)+len(held)*state['reserve']
    assert state['spent']+state['reserve']<=state['limit']==52631332
    assert billing['estimate']+(state['limit']-state['spent'])/1e6+10<=180
    return state,held,billing

def prepare():
    state,held,billing=guards();h,url=api()
    # Every remaining input still equals the frozen scientific package.
    files=read('package.json')['files'];verified=[]
    for i in range(1483,1531):
        for path in [f'inputs/items/{i}.json',f'inputs/wave-{i:06d}.xz']:
            local=R/'data/cloud07'/path;assert sha(local)==files[path]
            r=get(h,url,path);r.raise_for_status();m=r.json()
            assert m['md5Hash']==base64.b64encode(__import__('hashlib').md5(local.read_bytes()).digest()).decode()
            verified.append(dict(name=m['name'],generation=m['generation'],md5Hash=m['md5Hash']))
        for path in [f'claims/wave-{i:06d}.json',f'children/{i}.json']:assert get(h,url,path).status_code==404
    assert get(h,url,'continuation-7-claim.json').status_code==404
    assert get(h,url,f"epochs/{state['epoch']}/claim.json").status_code==404
    payload=dict(state=state,allocation_audit='november-terminal-audit.json',held_indices=held,prior_execution=read('status.json')['controller']['name'])
    contents=json.dumps(payload).encode();name='control/continuation-7.json'
    r=requests.post('https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o',params=dict(uploadType='media',name=PREFIX+name,ifGenerationMatch=0),headers=h,data=contents,timeout=60);r.raise_for_status()
    rr=requests.get(url+requests.utils.quote(PREFIX+name,safe=''),params=dict(alt='media',generation=r.json()['generation']),headers=h,timeout=60);rr.raise_for_status();assert rr.content==contents
    save('resume7-state.json',payload);save('resume7-input-verification.json',dict(passed=True,objects=verified))
    for src,dst in [('rolling07-resume6.yaml','rolling07-resume7.yaml'),('rolling07-nov3-check.yaml','rolling07-nov4-check.yaml')]:
        text=(R/src).read_text().replace('continuation-6','continuation-7').replace('t51r07-resume6','t51r07-resume7')
        if 'check' in dst:text=text.replace('858','1483').replace('0001483','001483')
        (R/dst).write_text(text)
    for name,file in [('t51r07-resume7','rolling07-resume7.yaml'),('t51r07-nov4-check','rolling07-nov4-check.yaml')]:
        gc('workflows','deploy',name,'--location=us-central1','--source='+str(R/file),'--service-account=fds-watchdog@'+PROJECT+'.iam.gserviceaccount.com')
        d=gc('workflows','describe',name,'--location=us-central1');assert yaml.safe_load(d['sourceContents'])==yaml.safe_load((R/file).read_text())
        save(name+'-deployed.json',dict(passed=True,sha256=sha(R/file),revision=d['revisionId']))
    e=gc('workflows','execute','t51r07-nov4-check','--location=us-central1');save('nov4-readiness-execution.json',e)
    for _ in range(90):
        d=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow=t51r07-nov4-check','--location=us-central1')
        if d['state'] not in ('ACTIVE','QUEUED'):break
        time.sleep(2)
    assert d['state']=='SUCCEEDED',d.get('error')
    children=json.loads(d['result'])['children'];assert len(children)==3
    for n in children:
        x=gc('workflows','executions','describe',n.split('/')[-1],'--workflow='+n.split('/')[-3],'--location=us-central1')
        assert x['state']=='SUCCEEDED' and json.loads(x['result'])['dry_run']
    save('nov4-readiness.json',dict(passed=True,execution=d));print('Prepared continuation 7; no simulations submitted',flush=True)

def launch():
    state,held,billing=guards();assert read('nov4-readiness.json')['passed'];assert read('resume7-unchanged-workers.json')['passed'];assert state==read('resume7-state.json')['state']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/codex/ignition-surrogate-pilot'],cwd=R,text=True).split()[0];assert head==remote
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip()
    h,url=api();assert get(h,url,'continuation-7-claim.json').status_code==404
    with (B.parent/'data/budget.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads(B.read_text());entry=ledger['reservations']['fds-tree51-nov06-continuation']
        assert entry['state']=='submitted' and ledger['reservations']['fds-tree51-training']['allowance_usd']==20
        assert round(entry['compute_limit_usd']*1e6)==state['limit'] and entry['spending_ceiling']==180
        with (P/'resume7-submission-intent.json').open('x') as f:json.dump(dict(time=time.time(),workflow='t51r07-resume7',cursor=1483,source=head),f)
        e=gc('workflows','execute','t51r07-resume7','--location=us-central1','--data={}')
        save('resume7-execution.json',e);entry.setdefault('continuations',[]).append(e['name'])
        entry['latest_allocation_reconciliation']=dict(receipt='private07/november-terminal-audit.json',held_indices=held,spent_microdollars=state['spent'])
        tmp=B.with_suffix('.resume7.tmp');tmp.write_text(json.dumps(ledger,indent=2)+'\n');tmp.replace(B)
    f=R/'continuation-record07.json';record=json.loads(f.read_text());record['previous_allocation_continuation']=record['latest_continuation'];record['latest_continuation']=dict(workflow='t51r07-resume7',execution=e['name'].split('/')[-1],created_at=e['startTime'],first_index=1483,remaining_never_submitted=48,local_admission_gate=False);f.write_text(json.dumps(record,indent=2)+'\n')
    print('Submitted once at untouched index 1483',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch']);a=p.parse_args();globals()[a.action]()
