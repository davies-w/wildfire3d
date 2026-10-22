import json,base64,zlib,io,hashlib
from pathlib import Path
import numpy as np,yaml
R=Path(__file__).parent;P=R.parent
case=next(c for c in json.loads((P/'cases.json').read_text()) if c['split']=='train');a=np.load(P/'data/fields'/(case['case']+'.npy'),mmap_mode='r');times=np.load(P/'data/fields'/(case['case']+'-time.npy'))
b=io.BytesIO();np.save(b,a[10:12,:,::4,::4,::4]);sample=b.getvalue()
payload={n:base64.b64encode((P/n).read_bytes()).decode() for n in ['models.py','original_cnn.py','previous_loss.py']}
payload.update({'benchmark_worker.py':base64.b64encode((R/'benchmark_worker.py').read_bytes()).decode(),'sample.npy':base64.b64encode(sample).decode(),'sample.json':base64.b64encode(json.dumps(dict(case,times=times[10:12].tolist())).encode()).decode()})
encoded=base64.b64encode(zlib.compress(json.dumps(payload).encode())).decode()
bootstrap="import pathlib,base64,zlib,json,sys,runpy; p=pathlib.Path('/tmp/study');p.mkdir(exist_ok=True);d=json.loads(zlib.decompress(base64.b64decode("+repr(encoded)+")));[(p/n).write_bytes(base64.b64decode(v)) for n,v in d.items()];sys.path.insert(0,str(p));runpy.run_path(str(p/'benchmark_worker.py'),run_name='__main__')"
w=json.loads((P.parent/'28_single_tree_repair/workflow-template.json').read_text());steps=w['main']['steps'];ass=steps[0]['initialize']['assign'];ass[0]['deadline']='${sys.now() + 3000}';ass.append({'queue_deadline':'${sys.now() + 1800}'})
job=ass[1]['job'];task=job['taskGroups'][0]['taskSpec'];task['maxRunDuration']='900s';task['maxRetryCount']=0
con=task['runnables'][0]['container'];con.update(imageUri='pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime',entrypoint='python',commands=['-c',bootstrap],options='--runtime=nvidia --shm-size=1g')
instance=job['allocationPolicy']['instances'][0];instance['installGpuDrivers']=True;instance['policy'].update(machineType='g2-standard-4',provisioningModel='SPOT');instance['policy']['bootDisk']={'sizeGb':'60','type':'pd-balanced'}
job['labels']['trial_id']='gpu29-test02';job['allocationPolicy']['labels']['trial_id']='gpu29-test02'
monitor=next(x['monitor'] for x in steps if 'monitor' in x)['try']['steps']
monitor.insert(1,{'get_vm':{'call':'http.get','args':{'url':'https://compute.googleapis.com/compute/v1/projects/tmrw-wildfire-20261015/zones/us-central1-a/instances','query':{'filter':'labels.trial_id = gpu29-test02'},'auth':{'type':'OAuth2'}},'result':'active_vms'}})
monitor.insert(2,{'reset_age':{'assign':[{'age_expired':False}]}})
monitor.insert(3,{'check_vm_age':{'for':{'value':'active_vm','in':'${default(map.get(active_vms.body, "items"), [])}','steps':[{'age_limit':{'switch':[{'condition':'${sys.now() >= time.parse(active_vm.creationTimestamp) + 1200}','assign':[{'age_expired':True}]}]}}]}}})
check=next(x['check'] for x in monitor if 'check' in x)['switch'];check.append({'condition':'${age_expired}','next':'record'});check.append({'condition':'${len(default(map.get(active_vms.body, "items"), [])) == 0 and sys.now() >= queue_deadline}','next':'record'})
raw=json.dumps(w).replace('fds-controlled-trial','fds-gpu29-test02').replace('domain17/job-status.json','gpu29/test02/job-status.json').replace('labels.trial_id = study17','labels.trial_id = gpu29-test02')
(R/'workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));(R/'results/input-manifest.json').write_text(json.dumps({'source_case':case,'frame_indices':[10,11],'target_shape':[2,6,12,8,8],'sample_sha256':hashlib.sha256(sample).hexdigest(),'payload_bytes':len(raw),'files':{n:hashlib.sha256(base64.b64decode(v)).hexdigest() for n,v in payload.items()}},indent=2));print('workflow bytes',len(raw));assert len(raw)<120000
