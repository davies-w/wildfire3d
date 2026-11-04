"""Build a non-launchable controller template with cloud-driven checkpoint adaptation.
Packaging must inject frozen job candidates and a reviewed budget gate before deployment.
"""
from pathlib import Path
import copy,json,yaml
R=Path(__file__).resolve().parent
RUN='fds-tree51-campaign01';PREFIX='tree51/campaign01/';BUCKET='tmrw-wildfire-20261015-trial'
def policy_steps():
 return [
 {'init':{'assign':[{'started':0},{'evicted':0},{'page':''},{'seconds':'${previous}'}]}},
 {'read_tasks':{'try':{'call':'http.get','args':{'url':'${"https://batch.googleapis.com/v1/projects/tmrw-wildfire-20261015/locations/"+c.region+"/jobs/"+c.job_id+"/taskGroups/group0/tasks"}','auth':{'type':'OAuth2'},'query':{'pageSize':100,'pageToken':'${page}','fields':'tasks(name,status(state,statusEvents(taskExecution(exitCode)))),nextPageToken'}},'result':'tasks'},'retry':'${http.default_retry}'}},
 {'count_tasks':{'for':{'value':'task','in':'${default(map.get(tasks.body,"tasks"),[])}','steps':[
  {'started_task':{'switch':[{'condition':'${task.status.state == "RUNNING" or task.status.state == "SUCCEEDED" or task.status.state == "FAILED"}','assign':[{'started':'${started+1}'}]}]}},
  {'clear_flag':{'assign':[{'preempted':False}]}},
  {'events':{'for':{'value':'event','in':'${default(map.get(task.status,"statusEvents"),[])}','steps':[
   {'confirmed':{'switch':[{'condition':'${default(map.get(event,["taskExecution","exitCode"]),0) == 50001}','assign':[{'preempted':True}]}]}}
  ]}}},
  {'count_once':{'switch':[{'condition':'${preempted}','assign':[{'evicted':'${evicted+1}'}]}]}}
 ]}}},
 {'next_page':{'assign':[{'page':'${default(map.get(tasks.body,"nextPageToken"),"")}'}]}},
 {'more':{'switch':[{'condition':'${page != ""}','next':'read_tasks'}]}},
 {'choose':{'switch':[
  {'condition':'${evicted >= 4 and evicted*10 >= started and seconds > 180}','assign':[{'seconds':180}]},
  {'condition':'${evicted >= 2 and evicted*20 >= started and seconds > 300}','assign':[{'seconds':300}]}
 ]}},
 {'publish_change':{'switch':[{'condition':'${seconds < previous}','steps':[
  {'publish':{'call':'http.post','args':{'url':f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o','auth':{'type':'OAuth2'},'query':{'uploadType':'media','name':'${"'+PREFIX+'control/"+string(seconds)+".json"}','ifGenerationMatch':0},'headers':{'Content-Type':'application/json'},'body':{'run_id':RUN,'checkpoint_seconds':'${seconds}','confirmed_preemptions':'${evicted}','started_tasks':'${started}','job':'${c.job_id}'}}}}
 ]}]}},
 {'done':{'return':'${seconds}'}}
 ]
def build():
 w=yaml.safe_load((R.parent/'50_live_oak/workflow.yaml').read_text())
 w=json.loads(json.dumps(w).replace('tree50/oak01/',PREFIX).replace('fds-tree50-oak01',RUN).replace('tree50-oak01','tree51-campaign01'))
 w['inventory']['steps'][1]['zones']['for']['steps'][3]['get_disks']['try']['args']['query']['filter']='name eq fds-tree51-campa.*'
 w['main']['steps'][0]['init']['assign']=[{'candidates':[]},{'checkpoint_seconds':480}]
 # Explicitly prevent execution of the development template.
 w['main']['steps'].insert(1,{'unpackaged_guard':{'raise':'UNPACKAGED: frozen cases, budget admission and preservation proof required'}})
 steps=w['main']['steps'][2]['campaign']['try']['steps'][0]['waves']['for']['steps']
 index=next(i for i,x in enumerate(steps) if 'terminal' in x)
 steps.insert(index,{'adapt_checkpoint_interval':{'call':'adapt_checkpoints','args':{'c':'${c}','previous':'${checkpoint_seconds}'},'result':'checkpoint_seconds'}})
 w['main']['steps'][-1]['done']['return']['cases']=2000
 w['main']['steps'][-1]['done']['return']['reused_cases']=22
 w['adapt_checkpoints']={'params':['c','previous'],'steps':policy_steps()}
 # Intended packaging inserts this initialization inside cleanup-protected campaign.
 w['initialize_checkpoint_control']={'steps':[{'publish_initial':{'call':'http.post','args':{'url':f'https://storage.googleapis.com/upload/storage/v1/b/{BUCKET}/o','auth':{'type':'OAuth2'},'query':{'uploadType':'media','name':PREFIX+'control/480.json','ifGenerationMatch':0},'headers':{'Content-Type':'application/json'},'body':{'run_id':RUN,'checkpoint_seconds':480}}}},{'done':{'return':True}}]}
 w['main']['steps'][2]['campaign']['try']['steps'].insert(0,{'initialize_policy':{'call':'initialize_checkpoint_control'}})
 (R/'controller-template.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
 return w
if __name__=='__main__':build()
