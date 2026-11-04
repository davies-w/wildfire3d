"""Build OFFLINE workflow templates. No credentials, network, deployment or ledger edits.

Render a unique namespace only after the active campaign is terminal and audited.
The templates intentionally use an unbound __RUN__ placeholder.
"""
import copy
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BUCKET = 'tmrw-wildfire-20261015-trial'
PREFIX = 'tree51/__RUN__/'
API = 'https://workflowexecutions.googleapis.com/v1/projects/tmrw-wildfire-20261015/locations/us-central1/workflows/'
AUTH = {'type': 'OAuth2'}
def expr(s): return '${' + s + '}'
def assign(**kw): return {'assign': [{k:v} for k,v in kw.items()]}
def step(name, value): return {name:value}
def get(url, result):
    return {'try': {'call':'http.get','args':{'url':url,'auth':AUTH},'result':result},'retry':'${http.default_retry}'}
def obj_read(name, result):
    return {'call':'http.get','args':{'url':expr('"https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/"+text.url_encode("'+PREFIX+'"+'+name+')'), 'auth':AUTH,'query':{'alt':'media'}},'result':result}
def post(url, body, result=None):
    d={'call':'http.post','args':{'url':url,'auth':AUTH,'body':body}}
    if result: d['result']=result
    return d

def immutable(name, body):
    return {'call':'http.post','args':{'url':'https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o','auth':AUTH,'query':{'uploadType':'media','name':expr('"'+PREFIX+'"+'+name),'ifGenerationMatch':0},'headers':{'Content-Type':'application/json'},'body':body}}

def case_workflow():
    doc=yaml.safe_load((EXP/'wave04.yaml').read_text())
    # Decode/rewrite the bootstrap, not just the visible YAML prefix.
    import base64, re
    raw=yaml.safe_dump(doc,sort_keys=False)
    raw=raw.replace('tree51/campaign04/', PREFIX).replace('tree51%2Fcampaign04%2F','tree51%2F__RUN__%2F')
    raw=raw.replace('fds-tree51-campaign04','__RUN__').replace('tree51-campaign04','__RUN__')
    doc=yaml.safe_load(raw)
    main=doc['main']['steps']; named={next(iter(s)):next(iter(s.values())) for s in main}
    template=named['init']['assign'][0]['template']
    command=template['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands'][1]
    encoded=re.search("b64decode\\('([^']+)'",command).group(1)
    decoded=base64.b64decode(encoded).decode().replace('tree51/campaign04/',PREFIX)
    command=command.replace(encoded,base64.b64encode(decoded.encode()).decode())
    template['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands'][1]=command
    # Read one indexed singleton item instead of loading/scanning 2,000 cases.
    main[:]=[s for s in main if next(iter(s)) not in ('read_manifest','select_wave')]
    pos=next(i for i,s in enumerate(main) if 'validate' in s)
    main[pos:pos]=[step('read_item',obj_read('"inputs/items/"+string(args.index)+".json"','item')),
                  step('select_item',assign(wave='${item.body}'))]
    named['validate']['switch'].insert(0, {'condition':'${wave.count != 1 or wave.index != args.index}', 'raise':'Singleton manifest mismatch'})
    run=named['wave_run']['try']['steps']; rn={next(iter(s)):next(iter(s.values())) for s in run}
    # Short unique names avoid the old 17-character campaign-prefix truncation.
    for a in rn['candidate']['assign']:
        if 'c.job_id' in a: a['c.job_id']='${"__RUN__-c"+string(args.index)}'
        if 'c.label' in a: a['c.label']='${c.job_id}'
    # Only the owner may clean this case's resources; never campaign-wide disks.
    zones=doc['inventory']['steps'][1]['zones']['for']['steps']
    for s in zones:
        if 'get_disks' in s:
            s['get_disks']['try']['args']['query']['filter']='${"labels.trial_id = " + c.label}'
        for lookup in ('get_disks','get_vms'):
            if lookup in s:
                q=s[lookup]['try']['args']['query']
                q['fields']=q['fields'].replace('selfLink,','selfLink,labels,')
        for guard in ('page_guard_v','page_guard_d'):
            if guard in s:
                s[guard]['switch'][1]['condition']=s[guard]['switch'][1]['condition'].replace('> 18','> 1')
    # Check response ownership independently of the server's filter.
    for s in zones:
        for key,kind in [('append_vms','vm'),('append_disks','disk')]:
            if key in s:
                s[key]['for']['steps'].insert(0,step('ownership_'+kind,{'switch':[{'condition':expr('map.get('+kind+',["labels","trial_id"]) != c.label'),'raise':'Foreign resource in case cleanup inventory'}]}))
    for s in doc['cleanup']['steps']:
        if 'empty' in s: s['empty']['switch'][0]['next']='cleanup_count'
        if 'job_wait' in s: s['job_wait']['switch'][0]['next']='cleanup_count'
    named['init']['assign'].append({'started_reported':False})
    marksteps=[step('publish_started',immutable('"started/"+string(args.index)+".json"',{'started':True})),step('remember_started',assign(started_reported=True))]
    rp=next(i for i,s in enumerate(run) if 'terminal' in s)
    run[rp:rp]=[step('report_started',{'switch':[{'condition':'${not started_reported and (int(default(map.get(state.body,["status","taskGroups","group0","counts","RUNNING"]),0))>0 or state.body.status.state=="SUCCEEDED")}','steps':copy.deepcopy(marksteps)}]})]
    # No case-local policy reduction: global scheduler owns policy across slots.
    run[:]=[s for s in run if 'eviction_check_needed' not in s]
    doc.pop('adapt_checkpoints')
    rn['terminal']['switch'][1]={'condition':'${state.body.status.state == "FAILED"}','next':'failed_task'}
    # Read failed task events once before cleanup; classify ONLY numeric 50001.
    fp=next(i for i,s in enumerate(run) if 'clean_success' in s)
    run[fp:fp]=[
      step('failed_task',get('${"https://batch.googleapis.com/v1/projects/tmrw-wildfire-20261015/locations/us-central1/jobs/"+c.job_id+"/taskGroups/group0/tasks"}','failed')),
      step('failed_shape',{'switch':[{'condition':'${len(default(map.get(failed.body,"tasks"),[]))!=1 or map.get(failed.body,"nextPageToken")!=null or failed.body.tasks[0].status.state!="FAILED"}','raise':'Unexpected singleton task status'}]}),
      step('failed_init',assign(spot=False,events='${default(map.get(failed.body.tasks[0],["status","statusEvents"]),[])}')),
      step('failed_bound',{'switch':[{'condition':'${len(events)>50}','raise':'Failed task history exceeds audit bound'}]}),
      step('failed_events',{'for':{'value':'event','in':'${events}','steps':[step('spot_event',{'switch':[{'condition':'${default(map.get(event,["taskExecution","exitCode"]),0)==50001}','assign':[{'spot':True}]}]})]}}),
      step('report_evicted_start',{'switch':[{'condition':'${spot and not started_reported}','steps':copy.deepcopy(marksteps)}]}),
      step('pin_failed_task',immutable('c.id+"/failed-task.json"','${failed.body}')),
      step('clean_failure',{'call':'cleanup','args':{'c':'${c}'}}),
      step('failed_result',{'return':{'passed':False,'wave':'${wave.id}','count':1,'cleanup_verified':True,'spot':'${spot}','started':'${started_reported}','compute_charge_upper_usd':'${(sys.now()-wave_started)*admission.body.rate_usd_per_vm_hour/3600}'}}),
    ]
    rn['wave_result']['return'].update(spot=False,started=True)
    return doc

def epoch_workflow():
    # Only one epoch owns admission. Claim before any execution POST; no POST retry.
    steps=[step('init',assign(s='${args.state}',ticks=0)),
      step('claim_epoch',immutable('"epochs/"+string(s.epoch)+"/claim.json"',{'execution':'${sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}'})),
      step('read_admission',obj_read('"control/admission-v4.json"','admission')),
      step('validate',{'switch':[{'condition':'${admission.body.passed != true or s.reserve != 525000 or s.limit < 0 or s.limit > int(admission.body.compute_limit_usd*1000000) or len(s.active)>18}','raise':'Invalid admission/state'}]}),
      step('poll',{'for':{'value':'key','in':'${keys(s.active)}','steps':[
        step('started_marker',{'switch':[{'condition':'${not s.active[key].started}','steps':[
          step('read_started',{'try':obj_read('"started/"+key+".json"','marker'),'except':{'as':'err','steps':[step('missing_only',{'switch':[{'condition':'${map.get(err,"code")!=404}','raise':'${err}'}]}),step('no_marker',assign(marker={'body':{'started':False}}))]}}),
          step('record_started',{'switch':[{'condition':'${marker.body.started}','assign':[{'s.active[key].started':True},{'s.started':'${s.started+1}'}]}]})
        ]}]}),
        step('get_case',get('${"https://workflowexecutions.googleapis.com/v1/"+s.active[key].execution}','child')),
        step('child_state',{'switch':[
          {'condition':'${child.body.state=="ACTIVE" or child.body.state=="QUEUED"}','next':'continue'},
          {'condition':'${child.body.state!="SUCCEEDED"}','steps':[step('halt_unknown',assign(**{'s.stopped':True,'s.audit_required':True}))],'next':'continue'}]}),
        step('decode',assign(outcome='${json.decode(child.body.result)}')),
        step('validate_outcome',{'switch':[{'condition':'${outcome.cleanup_verified!=true or outcome.count!=1 or outcome.wave!=s.active[key].wave or outcome.compute_charge_upper_usd<0 or outcome.compute_charge_upper_usd*1000000>s.reserve}','raise':'Invalid case outcome; retain reservations and audit'}]}),
        step('pin_outcome',immutable('"outcomes/"+key+".json"','${outcome}')),
        step('final_started',{'switch':[{'condition':'${outcome.started and not s.active[key].started}','assign':[{'s.started':'${s.started+1}'}]}]}),
        step('settle',assign(**{'s.spent':'${s.spent-int(math.floor(-outcome.compute_charge_upper_usd*1000000))}','s.active':'${map.delete(s.active,key)}'})),
        step('count_evicted',{'switch':[{'condition':'${outcome.spot}','assign':[{'s.evicted':'${s.evicted+1}'}]}]}),
        step('success_or_drain',{'switch':[{'condition':'${outcome.passed}','assign':[{'s.completed':'${s.completed+1}'}]},{'condition':'${true}','assign':[{'s.stopped':True}]}]}),
      ]}}),
      step('policy',assign(new_policy='${s.policy}')),
      step('thresholds',{'switch':[{'condition':'${s.evicted>=4 and s.evicted*10>=s.started}','assign':[{'new_policy':180}]},{'condition':'${s.evicted>=2 and s.evicted*20>=s.started and s.policy>300}','assign':[{'new_policy':300}]}]}),
      step('publish_policy',{'switch':[{'condition':'${new_policy<s.policy}','steps':[step('policy_marker',immutable('"control/"+string(new_policy)+".json"',{'run_id':'__RUN__','checkpoint_seconds':'${new_policy}'})),step('policy_set',assign(**{'s.policy':'${new_policy}'}))]}]}),
      step('admit',{'switch':[{'condition':'${s.stopped or s.cursor>=s.total or len(s.active)>=18 or s.spent+(len(s.active)+1)*s.reserve>s.limit}','next':'end_tick'}]}),
      step('read_item',obj_read('"inputs/items/"+string(s.cursor)+".json"','item')),
      step('check_item',{'switch':[{'condition':'${item.body.index!=s.cursor or item.body.count!=1}','raise':'Invalid singleton input'}]}),
      step('intent',immutable('"intents/"+string(s.cursor)+".json"',{'index':'${s.cursor}','reserved_micro_usd':'${s.reserve}','epoch':'${s.epoch}'})),
      step('case_args',assign(child_args={'index':'${s.cursor}','wave_id':'${item.body.id}','spent':'${s.spent/1000000.0}','checkpoint_seconds':'${s.policy}'})),
      step('submit',post(API+'__RUN__-case/executions',{'argument':'${json.encode_to_string(child_args)}'},'created')),
      step('remember',assign(key='${string(s.cursor)}')),
      step('active_add',{'assign':[{'s.active[key]':{'execution':'${created.body.name}','wave':'${item.body.id}','started':False}},{'s.cursor':'${s.cursor+1}'}]}),
      step('pin_submission',immutable('"children/"+key+".json"','${created.body}')),
      step('more_slots',{'assign':[{'ticks':'${ticks}'}],'next':'admit'}),
      step('end_tick',assign(ticks='${ticks+1}')),
      step('bounds',{'switch':[
        {'condition':'${s.audit_required}','next':'handoff'},
        {'condition':'${len(s.active)==0 and (s.stopped or s.cursor>=s.total or s.spent+s.reserve>s.limit)}','next':'handoff'},
        {'condition':'${ticks>=60}','next':'handoff'}]}),
      step('sleep',{'call':'sys.sleep','args':{'seconds':30},'next':'poll'}),
      step('handoff',assign(**{'s.epoch':'${s.epoch+1}'})),
      step('pin_handoff',immutable('"handoffs/"+string(s.epoch)+".json"','${s}')),
      step('return',{'return':'${s}'}),
    ]
    return {'main':{'params':['args'],'steps':steps}}

def parent_workflow():
    return {'main':{'params':['args'],'steps':[
      step('admission',obj_read('"control/admission-v4.json"','admission')),
      step('manifest',obj_read('"inputs/index.json"','index')),
      step('validate',{'switch':[{'condition':'${admission.body.passed!=true or index.body.reviewed!=true or not (index.body.checkpoint_seconds==480 or index.body.checkpoint_seconds==300 or index.body.checkpoint_seconds==180)}','raise':'Unreviewed admission/manifest'}]}),
      step('owner_claim',immutable('"controller-claim.json"',{'execution':'${sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}'})),
      step('init',assign(s={'epoch':0,'cursor':0,'total':'${index.body.count}','active':{},'spent':0,'limit':'${int(admission.body.compute_limit_usd*1000000)}','reserve':525000,'started':0,'evicted':0,'policy':'${index.body.checkpoint_seconds}','completed':'${index.body.prior_completed}','stopped':False,'audit_required':False},polls=0,start='${sys.now()}')),
      step('initial_policy',immutable('"control/480.json"',{'run_id':'__RUN__','checkpoint_seconds':480})),
      step('inherited_policy',{'switch':[{'condition':'${s.policy<480}','steps':[step('initial_reduction',immutable('"control/"+string(s.policy)+".json"',{'run_id':'__RUN__','checkpoint_seconds':'${s.policy}'}))]}]}),
      step('epoch_args',assign(child_args={'state':'${s}'})),
      step('launch_epoch',post(API+'__RUN__-epoch/executions',{'argument':'${json.encode_to_string(child_args)}'},'epoch')),
      step('pin_epoch',immutable('"epochs/"+string(s.epoch)+"/execution.json"','${epoch.body}')),
      step('get_epoch',get('${"https://workflowexecutions.googleapis.com/v1/"+epoch.body.name}','status')),
      step('count',assign(polls='${polls+1}')),
      step('bound',{'switch':[{'condition':'${polls>10000 or sys.now()-start>259200}','raise':'Parent deadline; audit active epoch and cases'}]}),
      step('state',{'switch':[{'condition':'${status.body.state=="SUCCEEDED"}','next':'decode'},{'condition':'${status.body.state!="ACTIVE" and status.body.state!="QUEUED"}','raise':'Epoch failed; inspect immutable claims and active children; do not restart'}]}),
      step('wait',{'call':'sys.sleep','args':{'seconds':30},'next':'get_epoch'}),
      step('decode',assign(s='${json.decode(status.body.result)}')),
      step('next',{'switch':[{'condition':'${s.audit_required}','next':'done'},{'condition':'${len(s.active)>0 or (not s.stopped and s.cursor<s.total and s.spent+s.reserve<=s.limit)}','next':'epoch_args'}]}),
      step('done',{'return':{'state':'${s}','target_complete':False,'requires_allocation_and_scientific_audit':True}}),
    ]}}

def build():
    return {'parent.yaml':parent_workflow(),'epoch.yaml':epoch_workflow(),'case.yaml':case_workflow()}

class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data): return True

if __name__=='__main__':
    for name,doc in build().items():
        (HERE/name).write_text(yaml.dump(doc,Dumper=Dumper,sort_keys=False,width=120))
    print('Offline templates generated; __RUN__ is intentionally unbound. Nothing deployed.')
