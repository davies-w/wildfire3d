"""Build recovery-only controls; never submit or alter existing job identities."""
from cloud07 import *
import copy,yaml,math
case=yaml.safe_load((R/'rolling07-case.yaml').read_text())
q=case['await_quota']['steps'];q.insert(0,{'quota_bound':{'assign':[{'until':'${sys.now()+1800}'}]}})
q.insert(2,{'quota_shape':{'switch':[{'condition':'${map.get(q.body,"quotas")==null}','next':'quota_wait'}]}})
q[-1]={'quota_wait':{'switch':[{'condition':'${sys.now()>=until}','return':False}], 'next':'quota_sleep'}}
q[-2]['ready']['next']='quota_wait'
q.append({'quota_sleep':{'call':'sys.sleep','args':{'seconds':30},'next':'get'}})
run=next(s['wave_run']['try']['steps'] for s in case['main']['steps'] if 'wave_run' in s)
pos=next(i for i,s in enumerate(run) if 'quota_gate' in s);run[pos]['quota_gate']['result']='quota_ready';run.insert(pos+1,{'quota_available':{'switch':[{'condition':'${not quota_ready}','next':'admission_deferred'}]}})
pos=next(i for i,s in enumerate(run) if 'create' in s);original=run[pos]['create'];run[pos]['create']={'try':original,'except':{'as':'submission_error','steps':[{'only_transient':{'switch':[{'condition':'${not (map.get(submission_error,"code") in [429,500,502,503,504])}','raise':'${submission_error}'}]}},{'reconcile_until':{'assign':[{'reconcile_deadline':'${sys.now()+600}'}]}},{'reconcile':{'try':{'call':'http.get','args':{'url':'${"https://batch.googleapis.com/v1/projects/tmrw-wildfire-20261015/locations/us-central1/jobs/"+c.job_id}','auth':{'type':'OAuth2'}},'result':'existing'},'retry':'${http.default_retry}','except':{'as':'missing','steps':[{'only_missing':{'switch':[{'condition':'${map.get(missing,"code")!=404}','raise':'${missing}'}]}},{'not_observed':{'switch':[{'condition':'${sys.now()>=reconcile_deadline}','next':'deferred_inventory'}]}},{'reconcile_wait':{'call':'sys.sleep','args':{'seconds':30},'next':'reconcile'}}]}}},{'existing_owner':{'switch':[{'condition':'${existing.body.name!="projects/tmrw-wildfire-20261015/locations/us-central1/jobs/"+c.job_id or map.get(existing.body,["labels","trial_id"])!=c.label}','raise':'Submission reconciliation ownership mismatch'}]}}]}}
# These branches return a conservative charge, retain the case for later review and never retry its POST.
run.extend([{'deferred_inventory':{'call':'inventory','args':{'c':'${c}'},'result':'unsubmitted_inventory'}},{'deferred_empty':{'switch':[{'condition':'${len(unsubmitted_inventory.vms)>0 or len(unsubmitted_inventory.disks)>0}','raise':'Ambiguous submission resources require audit'}]}},{'admission_deferred':{'return':{'passed':False,'wave':'${wave.id}','count':1,'cleanup_verified':True,'spot':False,'started':False,'admission_deferred':True,'compute_charge_upper_usd':0.525}}}])
epoch=yaml.safe_load((R/'rolling07-epoch-ungated.yaml').read_text());poll=next(s['poll']['for']['steps'] for s in epoch['main']['steps'] if 'poll' in s)
switch=next(s['success_or_drain']['switch'] for s in poll if 'success_or_drain' in s);switch.insert(1,{'condition':'${default(map.get(outcome,"admission_deferred"),false)}','assign':[{'s.interrupted':'${s.interrupted+1}'}]})
for name,doc in [('case',case),('epoch',epoch)]:
 (R/f'rolling07-{name}-continuous.yaml').write_text(yaml.safe_dump(doc,sort_keys=False))
assert 'canary_gate' not in (R/'rolling07-epoch-continuous.yaml').read_text()
assert run[pos]['create']['try']==original and 'retry' not in run[pos]['create']
print('Built continuous quota wait and nonretrying submission reconciliation')
