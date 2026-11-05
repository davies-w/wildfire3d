"""Read-only object inventory and pinned small worker proofs; never submits jobs."""
from cloud07 import *
import requests,base64
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
session=requests.Session();session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,allowed_methods=['GET'],status_forcelist=[429,500,502,503,504])));session.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
_original_get=session.get
def refreshed_get(*args,**kwargs):
 response=_original_get(*args,**kwargs)
 if response.status_code==401:
  session.headers['Authorization']='Bearer '+subprocess.check_output([G,'auth','print-access-token'],text=True).strip()
  response=_original_get(*args,**kwargs)
 return response
session.get=refreshed_get
items=[];params={'prefix':PREFIX}
while True:
 response=session.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o',params=params,timeout=60);response.raise_for_status();v=response.json();items+=v.get('items',[])
 if not v.get('nextPageToken'):break
 params['pageToken']=v['nextPageToken']
cached={x['name']:x for x in json.loads((P/'worker-proofs.json').read_text())} if (P/'worker-proofs.json').exists() else {}
latest_jobs={}
for v in items:
 if '/job-status.json.' in v['name']:
  key=v['name'].split('/job-status.json.')[0];old=latest_jobs.get(key)
  if old is None or float(v['name'].split('/job-status.json.')[1])>float(old['name'].split('/job-status.json.')[1]):latest_jobs[key]=v
job_names={v['name'] for v in latest_jobs.values()}
proofs=[]
for v in items:
 if not v['name'].endswith(('/restore.json','/startup.json','/completion.json','/verified.json','/failed-task.json')) and not v['name'].startswith(PREFIX+'outcomes/') and v['name'] not in job_names:continue
 old=cached.get(v['name'])
 if old and old['generation']==v['generation'] and old['md5']==v['md5Hash']:
  proofs.append(old);continue
 assert int(v['size'])<20*1024**2
 response=session.get('https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+requests.utils.quote(v['name'],safe=''),params={'alt':'media','generation':v['generation']},timeout=60);response.raise_for_status();data=response.content
 assert base64.b64encode(hashlib.md5(data).digest()).decode()==v['md5Hash']
 proof=json.loads(data);proofs.append(dict(name=v['name'],generation=v['generation'],md5=v['md5Hash'],sha256=hashlib.sha256(data).hexdigest(),proof=proof))
save('objects.json',items);save('worker-proofs.json',proofs)
print(json.dumps(dict(objects=len(items),startups=[x['name'] for x in proofs if x['name'].endswith('/startup.json') and x['proof']['passed']],completed=[dict(name=x['name'],passed=x['proof']['passed']) for x in proofs if x['name'].endswith('/completion.json')],checkpoint_manifests=sum(x['name'].endswith('/verified.json') for x in proofs)),indent=2))
