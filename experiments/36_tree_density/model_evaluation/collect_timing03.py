"""Collect existing CUDA timing evidence without creating compute or granting access."""
import base64,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,BUCKET,gc,read,download_summary,save

def main():
 e=read('results/model-timing03-execution.json')['name'].split('/')
 status=gc('workflows','executions','describe',e[-1],'--workflow='+e[-3],'--location=us-central1')
 save('results/model-timing03-status.json',status)
 if status['state']=='ACTIVE':print('PREFLIGHT_ACTIVE');return
 root=R/'data/model-timing03-results';root.mkdir(exist_ok=True)
 inv={k:gc(*args,'--filter=labels.trial_id=gpu36-preflight03') for k,args in {'jobs':('batch','jobs','list','--location=us-central1'),'instances':('compute','instances','list'),'disks':('compute','disks','list')}.items()}
 save('results/model-timing03-cleanup.json',inv);assert not any(inv.values()),inv
 prefix='gs://'+BUCKET+'/density36/model-preflight03/';download_summary(prefix+'job-status.json',root/'job-status.json')
 assert json.loads((root/'job-status.json').read_text())['status']['state']=='SUCCEEDED','Diagnose cloud preflight failure; do not resubmit'
 files={}
 for name in ('cuda-check.json','evaluation-cloud-check.json','transport-cloud-check.json','timing.json','report-equivalence.json','complete.json'):
  meta=gc('storage','objects','describe',prefix+name);download_summary(prefix+name,root/name);data=(root/name).read_bytes()
  assert len(data)==int(meta['size']) and base64.b64encode(hashlib.md5(data).digest()).decode()==meta['md5_hash']
  assert json.loads(data)['passed'];files[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'generation':meta['generation']}
 report={'passed':True,'training':False,'cleanup_verified':True,'files':files,'permission_removal_pending':True}
 save('results/model-timing03-collected.json',report);print(json.dumps(report))
if __name__=='__main__':main()
