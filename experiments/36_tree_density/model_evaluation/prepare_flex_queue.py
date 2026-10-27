"""Prepare fixed-order remaining pairs; Flex-start queue, conservative conditional budget."""
from pathlib import Path
import json,hashlib,tarfile,io,base64,copy,yaml,shutil
R=Path(__file__).resolve().parents[1];D=R/'data/flex-queue';S=R/'data/pair-sequence/rotation1';PREFIX='density36/flex-queue01/';P='tmrw-wildfire-20261015';B=P+'-trial';ZONES=['us-central1-a','us-central1-b','us-central1-c']
def http(method,url,result=None,query=None,body=None):
 d={'call':'http.'+method,'args':{'url':url,'auth':{'type':'OAuth2'}}}
 if result:d['result']=result
 if query is not None:d['args']['query']=query
 if body is not None:d['args'].update(body=body,headers={'Content-Type':'application/json'})
 return d
def upload(name,body):return http('post','https://storage.googleapis.com/upload/storage/v1/b/'+B+'/o',query={'uploadType':'media','name':name,'ifGenerationMatch':0},body=body)
def main():
 assert not (R/'results/flex-queue-execution.json').exists()
 assert json.loads((R/'results/pair-sequence-cost-reconciled.json').read_text())['headroom']>=40
 original=json.loads((R/'results/pair-sequence-prepared.json').read_text())['packages'][1];names=list(original['files']);full=json.loads((R/'learning-schema.json').read_text());D.mkdir(exist_ok=True);packages=[];queue=[]
 for n in range(1,10):
  t=D/f'rotation{n}';(t/'data').mkdir(parents=True,exist_ok=True);prefix=PREFIX+f'rotation{n}/'
  for f in names:shutil.copyfile(S/f,t/f)
  (t/'runtime.py').write_text((S/'runtime.py').read_text().replace('density36/pair-sequence01/rotation1/',prefix))
  meta=json.loads((S/'schema.json').read_text());meta['rotations']=[full['rotations'][n]];meta['comparison']=f'Matched plain and soft-gated stride-one pair, fixed rotation{n}';(t/'schema.json').write_text(json.dumps(meta,indent=2)+'\n')
  plan=json.loads((S/'coverage-plan.json').read_text());plan.update(experiment=f'Density36 matched stride-one pair rotation{n}',test=f'Shared fixed rotation{n} test fold');(t/'coverage-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
  rot=meta['rotations'][0];sets=[set(rot[k]) for k in ('train','validation','test')];assert set.union(*sets)==set(range(2080)) and all(sets[i].isdisjoint(sets[j]) for i,j in ((0,1),(0,2),(1,2)))
  for f in names:
   if f not in ('runtime.py','schema.json','coverage-plan.json'):assert (S/f).read_bytes()==(t/f).read_bytes()
  hashes={f:hashlib.sha256((t/f).read_bytes()).hexdigest() for f in names}
  with tarfile.open(t/'inputs.tar','w') as tar:
   for f,b in [(f,(t/f).read_bytes()) for f in names]+[('hashes.json',json.dumps(hashes,sort_keys=True).encode())]:
    i=tarfile.TarInfo(f);i.size=len(b);tar.addfile(i,io.BytesIO(b))
  boot=(S/'bootstrap.py').read_text().replace('density36/pair-sequence01/rotation1/',prefix);(t/'bootstrap.py').write_text(boot)
  job=yaml.safe_load((S/'workflow.yaml').read_text())['main']['steps'][0]['initialize']['assign'][1]['job'];label=f'gpu36-flex01-r{n}'
  job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(boot.encode()).decode())+"),'bootstrap','exec'))"]
  job['allocationPolicy']['instances'][0]['policy'].update(provisioningModel='FLEX_START',reservation='NO_RESERVATION');job['allocationPolicy']['location']['allowedLocations']=['zones/'+z for z in ZONES];job['labels']['trial_id']=label;job['allocationPolicy']['labels']['trial_id']=label
  queue.append(dict(rotation=n,prefix=prefix,label=label,job_id='fds-'+label,job=job));packages.append(dict(rotation=n,prefix=prefix,sha256=hashlib.sha256((t/'inputs.tar').read_bytes()).hexdigest(),bytes=(t/'inputs.tar').stat().st_size,files=hashes,counts={k:len(rot[k]) for k in ('train','validation','test')}))
 # Reuse the proven single-job monitor and cleanup, parameterized across supported zones.
 child=copy.deepcopy(yaml.safe_load((S/'workflow.yaml').read_text())['main']);child['params']=['job','job_id','label','prefix'];steps=child['steps'];steps[0]['initialize']['assign']=[{'deadline':'${sys.now() + 154800}'},{'queue_deadline':'${sys.now() + 86400}'},{'status':{'body':{'status':{'state':'UNKNOWN'}}}},{'first_allocated':None}]
 batch='https://batch.googleapis.com/v1/projects/'+P+'/locations/us-central1/jobs/'
 def rewrite(x):
  if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
  if isinstance(x,list):return [rewrite(v) for v in x]
  if isinstance(x,str):
   return x.replace(batch+'fds-gpu36-seq01-r1','${"'+batch+'" + job_id}').replace('fds-gpu36-seq01-r1','${job_id}').replace('density36/pair-sequence01/rotation1/job-status.json','${prefix + "job-status.json"}')
  return x
 child=rewrite(child);steps=child['steps'];monitor=steps[2]['monitor']['try']['steps']
 monitor[1]={'get_vm':{'call':'list_resources','args':{'label':'${label}','kind':'instances'},'result':'active_vms'}}
 for step in monitor:
  if 'check_vm_age' in step:
   loop=step['check_vm_age']['for'];loop['in']='${active_vms}';loop['steps'].insert(0,{'first_allocation':{'switch':[{'condition':'${first_allocated == null or time.parse(active_vm.creationTimestamp) < first_allocated}','assign':[{'first_allocated':'${time.parse(active_vm.creationTimestamp)}'}]}]}})
  if 'check' in step:
   for condition in step['check']['switch']:
    condition['condition']=condition['condition'].replace('len(default(map.get(active_vms.body, "items"), []))','len(active_vms)')
 for idx,step in enumerate(steps):
  if 'list_workers' in step:steps[idx]={'list_workers':{'call':'list_resources','args':{'label':'${label}','kind':'instances'},'result':'workers'}}
  if 'delete_stragglers' in step:
   step['delete_stragglers']['for']['in']='${workers}';step['delete_stragglers']['for']['steps'][0]['delete_vm']['try']['args']['url']='${vm.selfLink}'
  if 'verify' in step:steps[idx]={'verify':{'call':'list_resources','args':{'label':'${label}','kind':'instances'},'result':'remaining'}}
  if 'assert_empty' in step:step['assert_empty']['switch'][0]['condition']='${len(remaining) > 0}'
  if 'done' in step:step['done']['return'].update(cost_bound_usd='${if(first_allocated == null, 15.2, (sys.now() - default(first_allocated,sys.now())) * 0.8 / 3600 + 0.1)}')
 # Verify disks are empty too; poll boundedly after job/VM deletion.
 steps[-1:-1]=[{'disk_deadline':{'assign':[{'disks_until':'${sys.now() + 300}'}]}},{'verify_disks':{'call':'list_resources','args':{'label':'${label}','kind':'disks'},'result':'disks'}},{'disk_gate':{'switch':[{'condition':'${len(disks) == 0}','next':'done'},{'condition':'${sys.now() >= disks_until}','raise':'Labeled disks remain after cleanup'}]}},{'disk_wait':{'call':'sys.sleep','args':{'seconds':15},'next':'verify_disks'}}]
 listing={'params':['label','kind'],'steps':[{'init':{'assign':[{'found':[]}]}},{'zones':{'for':{'value':'zone','in':ZONES,'steps':[{'read':http('get','${"https://compute.googleapis.com/compute/v1/projects/'+P+'/zones/" + zone + "/" + kind}','r',{'filter':'${"labels.trial_id = " + label}'})},{'items':{'for':{'value':'item','in':'${default(map.get(r.body,"items"),[])}','steps':[{'append':{'assign':[{'found':'${list.concat(found,item)}'}]}}]}}}]} }},{'done':{'return':'${found}'}}]}
 decode={'params':['value'],'steps':[{'map':{'switch':[{'condition':'${get_type(value) == "map"}','return':'${value}'}]}},{'decode':{'return':'${json.decode(value)}'}}]}
 mainsteps=[{'claim':upload(PREFIX+'lease.json',{'purpose':'Remaining fixed rotations1..9, no duplicates, 40USD bounded Flex-start queue'})},{'initialize':{'assign':[{'queue':queue},{'spent_bound':0.0},{'completed':[]},{'budget_stopped':False}]}},{'pairs':{'for':{'value':'item','in':'${queue}','steps':[{'budget_gate':{'switch':[{'condition':'${spent_bound + 15.2 > 40.0}','assign':[{'budget_stopped':True}],'next':'break'}]}},{'pair_intent':upload('${item.prefix + "launch-intent.json"}',{'rotation':'${item.rotation}','spent_bound':'${spent_bound}','reserved_pair_max':15.2})},{'run':{'call':'run_pair','args':{'job':'${item.job}','job_id':'${item.job_id}','label':'${item.label}','prefix':'${item.prefix}'},'result':'outcome'}},{'require_success':{'switch':[{'condition':'${outcome.final_state != "SUCCEEDED"}','raise':'Pair did not complete. No paid retry or later rotation launched.'}]}},{'complete':http('get','${"https://storage.googleapis.com/storage/v1/b/'+B+'/o/" + text.url_encode(item.prefix + "complete.json")}','completion',{'alt':'media'})},{'decode_complete':{'call':'decode_document','args':{'value':'${completion.body}'},'result':'complete_doc'}},{'freeze':http('get','${"https://storage.googleapis.com/storage/v1/b/'+B+'/o/" + text.url_encode(item.prefix + "selection-freeze.json")}','freeze_response',{'alt':'media'})},{'decode_freeze':{'call':'decode_document','args':{'value':'${freeze_response.body}'},'result':'freeze_doc'}},{'completion_gate':{'switch':[{'condition':'${complete_doc.success != true or complete_doc.folds != 2 or len(freeze_doc.selected) != 2 or freeze_doc.test_not_evaluated_yet != true}','raise':'Pair completion/selection barrier invalid'}]}},{'account':{'assign':[{'spent_bound':'${spent_bound + outcome.cost_bound_usd}'},{'completed':'${list.concat(completed,item.rotation)}'}]}},{'record_pair':upload('${item.prefix + "queue-accounting.json"}',{'outcome':'${outcome}','spent_bound':'${spent_bound}','completed':'${completed}'})}]}}},{'after_pairs':{'switch':[{'condition':'${budget_stopped}','next':'budget_stop'}]}},{'all_done':upload(PREFIX+'queue-complete.json',{'completed':'${completed}','spent_bound':'${spent_bound}','reason':'all_remaining_rotations_completed'})},{'done':{'return':{'completed':'${completed}','spent_bound':'${spent_bound}'}}},{'budget_stop':upload(PREFIX+'queue-complete.json',{'completed':'${completed}','spent_bound':'${spent_bound}','reason':'Insufficient allowance for another full pair maximum; no recipe reduction'})},{'stopped':{'return':{'completed':'${completed}','spent_bound':'${spent_bound}','reason':'budget_gate'}}}]
 w={'main':{'steps':mainsteps},'run_pair':child,'list_resources':listing,'decode_document':decode};(D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));assert (D/'workflow.yaml').stat().st_size<128*1024
 # No GPU fixture exercises every zone/resource listing and mixed JSON decoding.
 checks=[{'instances':{'call':'list_resources','args':{'label':'gpu36-flex-readiness','kind':'instances'},'result':'v'}},{'disks':{'call':'list_resources','args':{'label':'gpu36-flex-readiness','kind':'disks'},'result':'d'}},{'done':{'return':{'passed':True,'instances':'${v}','disks':'${d}'}}}]
 (D/'readiness.yaml').write_text(yaml.safe_dump({'main':{'steps':checks},'list_resources':listing},sort_keys=False))
 proof=dict(prepared=True,submitted=False,workflow='fds-gpu36-flex-queue01',prefix=PREFIX,rotations=list(range(1,10)),queue_wait_seconds_per_pair=86400,training_soft_seconds=64800,vm_max_seconds=66600,absolute_pair_seconds=154800,queue_allowance_usd=40.0,pair_max_allowance_usd=15.2,rate_bound_usd_hour=.8,price_note='Conservative Standard upper bound; no unverified Flex discount assumed',budget_gate='Before each pair require spent_bound +15.2 <=40; charge observed VM lifetime at.8/hour+.1cleanup margin',maximum_concurrent_gpus=1,automatic_retries=0,selection_barrier='Both models selected before either test within each fixed rotation; no performance-based fold choice',packages=packages,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest())
 (R/'results/flex-queue-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print('Prepared',len(packages),'pairs; workflow bytes',(D/'workflow.yaml').stat().st_size)
if __name__=='__main__':main()
