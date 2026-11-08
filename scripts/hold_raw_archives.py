"""Temporarily protect exact inventoried raw archive generations from lifecycle deletion.
No bucket policy changes, cloud launches, deletion, or permission changes.
"""
import argparse, concurrent.futures, json, pathlib, subprocess, threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def main():
 p=argparse.ArgumentParser();p.add_argument('--inventory',type=pathlib.Path,required=True);p.add_argument('--receipts',type=pathlib.Path,required=True);a=p.parse_args()
 items=json.loads(a.inventory.read_text());items=[x for x in items if x['name'].endswith('/archive-manifest.json') or '.tar.gz.part' in x['name']]
 token=subprocess.check_output([str(pathlib.Path.home()/'.local/google-cloud-sdk/bin/gcloud'),'auth','print-access-token'],text=True).strip();local=threading.local()
 def hold(v):
  if not hasattr(local,'s'):
   local.s=requests.Session();local.s.headers['Authorization']='Bearer '+token
   local.s.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,allowed_methods=['GET'],status_forcelist=[429,500,502,503,504])))
  s=local.s;url='https://storage.googleapis.com/storage/v1/b/'+v['bucket']+'/o/'+requests.utils.quote(v['name'],safe='')
  params={'generation':v['generation']};q=s.get(url,params=params,timeout=90)
  if q.status_code==404:return {'name':v['name'],'generation':v['generation'],'missing':True}
  q.raise_for_status();cur=q.json();assert cur['md5Hash']==v['md5Hash'] and cur['size']==v['size']
  if not cur.get('temporaryHold'):
   q=s.patch(url,params={**params,'ifGenerationMatch':v['generation'],'ifMetagenerationMatch':cur['metageneration']},json={'temporaryHold':True},timeout=90);q.raise_for_status()
  q=s.get(url,params=params,timeout=90);q.raise_for_status();cur=q.json();assert cur['temporaryHold'] and cur['generation']==v['generation']
  return {'name':v['name'],'generation':v['generation'],'held':True}
 a.receipts.parent.mkdir(parents=True,exist_ok=True);results=[]
 with a.receipts.open('a') as f,concurrent.futures.ThreadPoolExecutor(12) as pool:
  for result in pool.map(hold,items):
   f.write(json.dumps(result)+'\n');f.flush();results.append(result)
   if len(results)%100==0:print('Verified holds',len(results),'/',len(items),flush=True)
 print('Finished',len(results),'held',sum(x.get('held',False) for x in results),'missing',sum(x.get('missing',False) for x in results),flush=True)
if __name__=='__main__':main()
