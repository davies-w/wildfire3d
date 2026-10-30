"""Verify and retain all preempted-run artifacts and the latest completed checkpoint."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64,torch
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET
inv={k:gc(*a,'--filter=labels.trial_id=gpu38-history01') for k,a in dict(jobs=('batch','jobs','list','--location=us-west1'),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(inv.values()),inv
prefix='history38/training01/';token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o'
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=120).read()
items=json.loads(get(base+'?'+urllib.parse.urlencode({'prefix':prefix,'maxResults':1000})));assert 'nextPageToken' not in items
root=R/'data/preempted01';root.mkdir(exist_ok=True);proof={}
assert sum(int(x['size']) for x in items['items'])<128*1024**2
for item in items['items']:
 name=item['name'][len(prefix):];assert Path(name).name==name
 blob=get(base+'/'+urllib.parse.quote(item['name'],safe='')+'?'+urllib.parse.urlencode({'alt':'media','generation':item['generation']}))
 assert len(blob)==int(item['size']) and base64.b64encode(hashlib.md5(blob).digest()).decode()==item['md5Hash']
 (root/name).write_bytes(blob);proof[name]=dict(metadata=item,sha256=hashlib.sha256(blob).hexdigest())
status=json.loads((root/'job-status.json').read_text());assert status['status']['state']=='FAILED' and 'Spot VM preemption with exit code 50001' in json.dumps(status['status'])
for n in ['timing-check','optimizer-resume-check','cuda-check','evaluation-cloud-check','transport-cloud-check','fold00-checkpoint-replay']:assert json.loads((root/(n+'.json')).read_text())['passed']
epochs=sorted(int(n[12:15]) for n in proof if n.startswith('fold00-epoch') and n.endswith('.pt')) if False else sorted(int(n.split('epoch')[1].split('.')[0]) for n in proof if n.startswith('fold00-epoch') and n.endswith('.pt'))
assert epochs==list(range(1,max(epochs)+1));latest=max(epochs);ck=torch.load(root/f'fold00-epoch{latest:03}.pt',map_location='cpu',weights_only=False)
assert ck['epoch']==latest and ck['rotation']==0 and ck['optimizer']['state'] and ck['rng'] and ck['history'][-1]['epoch']==latest
assert ck['schema_hash']==hashlib.sha256((R/'data/training01/schema.json').read_bytes()).hexdigest()
assert not any('test' in n or 'selected.pt' in n for n in proof)
report=dict(passed=True,diagnosis='Spot preemption exit50001',latest_epoch=latest,checkpoint=f'fold00-epoch{latest:03}.pt',next_epoch=latest+1,optimizer_nonempty=True,cleanup=inv,objects=proof)
(R/'results01/preemption-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='objects'}))
