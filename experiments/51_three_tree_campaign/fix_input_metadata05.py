"""Correct JSON MIME metadata before production; preserve generations and bytes."""
from cloud05 import *
import requests,concurrent.futures,urllib.parse
assert not (P/'submission-intent.json').exists()
token=subprocess.check_output([G,'auth','print-access-token'],text=True).strip();headers={'Authorization':'Bearer '+token}
records=json.loads((P/'input-uploads.json').read_text())
def fix(m):
 if not m['name'].endswith('.json'):return
 u='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(m['name'],safe='')
 r=requests.patch(u,headers=headers,params={'ifGenerationMatch':m['generation']},json={'contentType':'application/json'},timeout=60);r.raise_for_status();v=r.json();assert v['md5Hash']==m['md5Hash'] and v['generation']==m['generation'] and v['contentType']=='application/json'
 return dict(name=v['name'],generation=v['generation'],md5Hash=v['md5Hash'],contentType=v['contentType'])
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:out=list(pool.map(fix,records))
save('input-metadata-correction.json',dict(passed=True,objects=[x for x in out if x]))
old=json.loads((P/'readiness-execution.json').read_text());save('readiness-execution-initial.json',old)
save('readiness-execution.json',gc('workflows','execute',WF+'-check','--location=us-central1'))
print('JSON metadata corrected; new no-solver readiness submitted')
