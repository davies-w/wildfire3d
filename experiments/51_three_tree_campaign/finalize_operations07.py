"""Render and freeze approved rolling07 control source before submission intent."""
from cloud07 import *
import sys,yaml,copy
assert not (P/'submission-intent.json').exists()
sys.path.insert(0,str(R/'rolling_fallback'));from prepare_rolling import render
from build import Dumper
D=R/'data/cloud07'
for n,s in render(WF).items():
 (R/('rolling07-'+n)).write_text(s);(D/n).write_text(s)
case=yaml.safe_load((D/'case.yaml').read_text());auth={'type':'OAuth2'}
def get(path,result):return {'call':'http.get','args':{'url':'https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+(PREFIX+path).replace('/','%2F'),'query':{'alt':'media'},'auth':auth},'result':result}
c=dict(job_id=WF+'-check',label=WF+'-check',region='us-central1',zones=['us-central1-a','us-central1-b','us-central1-c'],job={'taskGroups':[{'taskCount':'18'}]})
steps=[{'read_admission':get('control/admission-v4.json','admission')},{'read_index':get('inputs/index.json','index')},{'shape':{'switch':[{'condition':'${admission.body.passed!=true or index.body.count!=1531 or index.body.prior_completed!=468 or index.body.reviewed!=true}','raise':'Invalid admission/index'}]}},
 {'task_list_access':{'try':{'call':'http.get','args':{'url':'https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/jobs/'+WF+'-check/taskGroups/group0/tasks','auth':auth,'query':{'pageSize':1}}},'except':{'as':'err','steps':[{'expected_missing':{'switch':[{'condition':'${map.get(err,"code")!=404}','raise':'${err}'}]}}]}}}]
for n in ['one','two']:
 steps.append({'write_'+n:{'call':'http.post','args':{'url':'https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o','auth':auth,'query':{'uploadType':'media','name':'${"'+PREFIX+'readiness/'+n+'/"+sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}','ifGenerationMatch':0},'headers':{'Content-Type':'application/json'},'body':{'passed':True}}}})
steps += [{'quota':{'call':'await_quota','args':{'c':c}}},{'inventory':{'call':'inventory','args':{'c':c},'result':'inv'}},{'empty':{'switch':[{'condition':'${len(inv.vms)>0 or len(inv.disks)>0}','raise':'Unexpected readiness resources'}]}},{'init_children':{'assign':[{'children':[]}]}}]
for kind in ['case','epoch','parent']:
 name=WF+('-'+kind if kind!='parent' else '')
 args={'dry_run':True}
 if kind=='case':args.update(index=0,wave_id='wave-000000',spent=0,checkpoint_seconds=480)
 steps += [{'probe_'+kind:{'call':'http.post','args':{'url':'https://workflowexecutions.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/workflows/'+name+'/executions','auth':auth,'body':{'argument':json.dumps(args)}},'result':'child_'+kind}}, {'record_'+kind:{'assign':[{'children':'${list.concat(children,child_'+kind+'.body.name)}'}]}}]
steps.append({'done':{'return':{'passed':True,'children':'${children}'}}})
check={'main':{'steps':steps},'inventory':case['inventory'],'await_quota':case['await_quota']}
s=yaml.dump(check,Dumper=Dumper,sort_keys=False);(R/'rolling07-check.yaml').write_text(s);(D/'check.yaml').write_text(s)
a=json.loads((P/'authorization.json').read_text());pkg=json.loads((P/'package.json').read_text());pkg['files']={str(f.relative_to(D)):sha(f) for f in sorted(D.rglob('*')) if f.is_file()};save('package.json',pkg)
save('controller-admission-v4.json',dict(passed=True,mode='bounded_rolling_may_stop_short',compute_limit_usd=a['compute_limit_usd'],rate_usd_per_vm_hour=.15,reserve_seconds_per_vm=12600,index_sha256=pkg['index_sha256'],prior_completed=468,pending_terminal_review=1))
print('Rolling07 controls frozen; no cloud submission')
