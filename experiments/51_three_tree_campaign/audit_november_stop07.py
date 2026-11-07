"""Read-only terminal allocation and child audit for the November budget stop."""
from datetime import datetime
import json, subprocess, time
import requests
from cloud07 import G,P,PROJECT,gc,save

def read(n): return json.loads((P/n).read_text())
def stamp(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def main():
    status=read('status.json'); state=json.loads(status['controller']['result'])['state']
    assert status['controller']['state']=='SUCCEEDED' and state['cursor']==1483 and not state['active']
    assert not state['stopped'] and not state['audit_required']
    empty={k:gc(*a,'--filter=name~t51r07') for k,a in {'jobs':('batch','jobs','list','--location=us-central1'),'vms':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
    assert not any(empty.values())
    h={'Authorization':'Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()}
    children=[]; token=None
    while True:
        q={'view':'FULL','pageSize':1000}
        if token:q['pageToken']=token
        r=requests.get('https://workflowexecutions.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/workflows/t51r07-nov2-case/executions',headers=h,params=q,timeout=90);r.raise_for_status();d=r.json()
        children.extend(d.get('executions',[]));token=d.get('nextPageToken')
        if not token:break
    real=[x for x in children if not json.loads(x.get('argument','{}')).get('dry_run')]
    indices=[json.loads(x['argument'])['index'] for x in real]
    assert len(indices)==len(set(indices)) and set(indices)==set(range(837,1483))
    assert all(x['state']=='SUCCEEDED' for x in real)
    assert all(json.loads(x['result'])['cleanup_verified'] for x in real)
    save('november-terminal-children.json',real)
    start=read('resume4b-execution.json')['startTime']
    query=('protoPayload.serviceName="compute.googleapis.com" AND protoPayload.resourceName=~"/instances/t51r07-c[0-9]+-" AND ((protoPayload.methodName:"instances.insert" AND operation.first=true) OR (protoPayload.methodName:"instances.delete" AND operation.last=true)) AND timestamp>="'+start+'"')
    events=gc('logging','read',query,'--limit=10000');assert len(events)<10000
    pairs={}
    for e in events:
        p=e['protoPayload']; vm=p['resourceName'].split('/zones/')[1]; key='insert' if p['methodName'].endswith('.insert') else 'delete'
        pairs.setdefault(vm,{'insert':[],'delete':[]})[key].append(stamp(e['timestamp']))
    assert pairs and all(x['insert'] and x['delete'] and max(x['delete'])>=min(x['insert']) for x in pairs.values())
    secs=sum(max(x['delete'])-min(x['insert']) for x in pairs.values())
    save('november-terminal-pairs.json',pairs)
    save('november-terminal-audit.json',dict(passed=True,checked_at=time.time(),empty=empty,children=len(real),cursor=1483,pairs=len(pairs),allocation_seconds=secs,compute_upper_usd=secs*.15/3600,state=state))
    print('Terminal audit passed',len(real),'children',len(pairs),'VM pairs',secs*.15/3600,'compute')
if __name__=='__main__': main()
