"""Budgeted batch manager. Every launch reserves its full allowance permanently."""
import argparse,base64,fcntl,json,shutil,subprocess,tarfile,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent
G='/Users/wdavies/.local/google-cloud-sdk/bin/gcloud';PROJECT='tmrw-wildfire-20261015'
def gc(*args):
    p=subprocess.run([G,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True,timeout=180)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout or '{}')
def prepare(specpath):
    spec=json.loads(Path(specpath).read_text());name=spec['name'];folder=ROOT/'batches'/name
    if folder.exists():raise RuntimeError('Batch already prepared; do not overwrite')
    assert spec['allowance_usd']>=spec['controller_seconds']/3600*.065744+spec['ancillary_allowance_usd']
    assert spec['controller_seconds']>=1800 and len({r['case'] for r in spec['cases']})==len(spec['cases'])
    spec['worker_seconds']=spec['controller_seconds']-900
    for n in ('data','results','decks'):(folder/n).mkdir(parents=True,exist_ok=True)
    (folder/'.gitignore').write_text('!/data/\n/data/*\n!/data/*.dvc\n!/data/.gitignore\n/__pycache__/\n')
    for n in ('base_scene.py','scene.py','worker.py','design.json'):shutil.copy2(ROOT/n,folder/n)
    runner=(ROOT/'runner.py').read_text().replace('composition19/','composition20/'+name+'/')
    (folder/'runner.py').write_text(runner)
    shutil.copytree(ROOT/'inputs',folder/'inputs')
    (folder/'batch.json').write_text(json.dumps(spec,indent=2)+'\n')
    w=json.loads((ROOT/'workflow_template.json').read_text());steps=w['main']['steps']
    a=steps[0]['initialize']['assign'];a[0]['deadline']='${sys.now() + '+str(spec['controller_seconds'])+'}'
    job=a[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']=str(spec['controller_seconds']-360)+'s'
    paths=[folder/n for n in ('base_scene.py','scene.py','worker.py','runner.py','design.json','batch.json')]+list((folder/'inputs').glob('*'))
    payload={str(p.relative_to(folder)):base64.b64encode(p.read_bytes()).decode() for p in paths}
    bootstrap="import pathlib,base64,runpy,sys; root=pathlib.Path('/study'); payload="+repr(payload)+"; [(root/n).parent.mkdir(parents=True,exist_ok=True) for n in payload]; [(root/n).write_bytes(base64.b64decode(v)) for n,v in payload.items()]; sys.path.insert(0,'/study'); runpy.run_path('/study/worker.py',run_name='__main__')"
    task['runnables'][0]['container']['commands']=['-c',bootstrap]
    label='c20-'+name;job['labels']['trial_id']=label;job['allocationPolicy']['labels']['trial_id']=label
    for step in steps:
        if 'record' in step:step['record']['try']['args']['query']['name']='composition20/'+name+'/job-status.json'
        for k in ('list_workers','verify'):
            if k in step:step[k]['args']['query']['filter']='labels.trial_id = '+label
        if 'done' in step:step['done']['return']['mode']='composition20-'+name
    (folder/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
    print('Prepared',name,'cases',len(spec['cases']),'allowance',spec['allowance_usd'])
def launch(name):
    folder=ROOT/'batches'/name;spec=json.loads((folder/'batch.json').read_text());workflow='fds-c20-'+name
    if any(len(c['layout'])==3 for c in spec['cases']):
        import hashlib
        frozen=json.loads((ROOT/'results/frozen-predictions.json').read_text())
        inputs=ROOT/'confirmation-inputs.json'
        assert hashlib.sha256(inputs.read_bytes()).hexdigest()==frozen['confirmation_inputs_sha256']
        assert json.loads(inputs.read_text())==spec['cases'],'Test inputs differ from frozen predictions'
        assert {r['kind'] for r in frozen['models']}=={'graph','additive','simple','ignition_only'}
    with (ROOT/'data/budget.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        ledger=json.loads((ROOT/'budget.json').read_text())
        assert not any(r['batch']==name for r in ledger['reservations']),'Already reserved; inspect existing execution instead'
        assert sum(r['allowance_usd'] for r in ledger['reservations'])+spec['allowance_usd']<=ledger['total_authorized_usd']
        assert all(r['completed'] for r in json.loads((ROOT/'results/preflight.json').read_text()))
        for w in gc('workflows','list','--location=us-central1'):
            assert not gc('workflows','executions','list',w['name'].split('/')[-1],'--location=us-central1','--filter=state=ACTIVE'),'Another controller active'
        assert not gc('batch','jobs','list','--location=us-central1') and not gc('compute','instances','list'),'Existing job or VM'
        template=gc('workflows','describe','fds-domain17','--location=us-central1')
        gc('workflows','deploy',workflow,'--location=us-central1','--source='+str(folder/'workflow.yaml'),'--service-account='+template['serviceAccount'])
        deployed=gc('workflows','describe',workflow,'--location=us-central1')
        assert yaml.safe_load(deployed['sourceContents'])==yaml.safe_load((folder/'workflow.yaml').read_text())
        j=yaml.safe_load(deployed['sourceContents'])['main']['steps'][0]['initialize']['assign'][1]['job']
        assert j['taskGroups'][0]['taskSpec']['maxRetryCount']==0
        assert j['allocationPolicy']['instances'][0]['policy']['provisioningModel']=='SPOT'
        reservation=dict(batch=name,allowance_usd=spec['allowance_usd'],reserved_unix=time.time(),state='reserved')
        ledger['reservations'].append(reservation);(ROOT/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n')
        result=gc('workflows','execute',workflow,'--location=us-central1')
        reservation.update(state='submitted',execution=result['name'])
        (ROOT/'budget.json').write_text(json.dumps(ledger,indent=2)+'\n')
        (folder/'results/execution.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
def status(name):
    folder=ROOT/'batches'/name;execution=json.loads((folder/'results/execution.json').read_text())['name'].split('/')[-1]
    s=gc('workflows','executions','describe',execution,'--workflow=fds-c20-'+name,'--location=us-central1')
    (folder/'results/status.json').write_text(json.dumps(s,indent=2)+'\n');print(name,s['state'])
    if s['state']!='ACTIVE':
        inventory={k:gc(*a) for k,a in {'instances':('compute','instances','list'),'disks':('compute','disks','list'),'jobs':('batch','jobs','list','--location=us-central1')}.items()}
        (folder/'results/cleanup.json').write_text(json.dumps(inventory,indent=2)+'\n')
        print('Resources remaining:',{k:len(v) for k,v in inventory.items()})
    return s
def fetch(name):
    folder=ROOT/'batches'/name;dest=folder/'data/downloads';dest.mkdir(exist_ok=True);out=folder/'data/cloud';out.mkdir(exist_ok=True)
    listing=subprocess.run([G,'storage','ls','gs://tmrw-wildfire-20261015-trial/composition20/'+name+'/*.tar.gz'],capture_output=True,text=True,check=True)
    for url in listing.stdout.splitlines():
        target=dest/url.rsplit('/',1)[-1]
        if not target.exists():subprocess.run([G,'storage','cp',url,str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        with tarfile.open(target) as t:t.extractall(out,filter='data')
    with tarfile.open(folder/'data/cloud-evidence.tar.gz','w:gz') as t:t.add(out,arcname='cloud')
    print('Fetched',len(listing.stdout.splitlines()),'archives')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','status','fetch']);p.add_argument('target');a=p.parse_args();globals()[a.action](a.target)
