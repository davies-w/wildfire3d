"""Verify and retain all preempted-run artifacts and the latest completed checkpoint."""
from pathlib import Path
import sys,json,subprocess,urllib.request,urllib.parse,hashlib,base64,torch
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,BUCKET
inv={k:gc(*a,'--filter=labels.trial_id=gpu38-history05') for k,a in dict(jobs=('batch','jobs','list','--location=us-central1'),instances=('compute','instances','list'),disks=('compute','disks','list')).items()};assert not any(inv.values()),inv
prefix='history38/training05/';token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();base='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o'
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=120).read()
items=json.loads(get(base+'?'+urllib.parse.urlencode({'prefix':prefix,'maxResults':1000})));assert 'nextPageToken' not in items
root=R/'data/preempted05';root.mkdir(exist_ok=True);proof={}
assert sum(int(x['size']) for x in items['items'])<128*1024**2
for item in items['items']:
 name=item['name'][len(prefix):];assert Path(name).name==name
 blob=get(base+'/'+urllib.parse.quote(item['name'],safe='')+'?'+urllib.parse.urlencode({'alt':'media','generation':item['generation']}))
 assert len(blob)==int(item['size']) and base64.b64encode(hashlib.md5(blob).digest()).decode()==item['md5Hash']
 (root/name).write_bytes(blob);proof[name]=dict(metadata=item,sha256=hashlib.sha256(blob).hexdigest())
status=json.loads((root/'job-status.json').read_text());assert status['status']['state']=='FAILED' and 'Spot VM preemption with exit code 50001' in json.dumps(status['status'])
assert status['status']['runDuration']=='0s'
assert not any(n.startswith('fold00-epoch') for n in proof)
p=json.loads((R/'results05/package.json').read_text())
assert proof['inputs.tar']['sha256']==p['input_sha256']
ckpath=R/'data/training05/data/resume/fold00.pt'
assert hashlib.sha256(ckpath.read_bytes()).hexdigest()==p['resume_sha256']
ck=torch.load(ckpath,map_location='cpu',weights_only=False)
assert ck['epoch']==88 and ck['optimizer']['state'] and ck['rng']
report=dict(passed=True,diagnosis='Spot preemption exit50001 before task started',latest_epoch=88,next_epoch=89,new_epochs=0,startup_proofs_available=False,checkpoint_source='data/preempted04/fold00-epoch088.pt',checkpoint_sha256=p['resume_sha256'],cleanup=inv,objects=proof)
(R/'results05/preemption-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='objects'}))
