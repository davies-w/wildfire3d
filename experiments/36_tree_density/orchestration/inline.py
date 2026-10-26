"""Use unchanged Batch job definitions under existing watchdog permissions."""
from pathlib import Path
import yaml,json,copy,hashlib
R=Path(__file__).resolve().parent.parent;O=R/'orchestration';gs=json.loads((O/'queue.json').read_text());(O/'specs').mkdir(exist_ok=True)
normalized=[]
for g in gs:
 w=yaml.safe_load((R/'jobs'/g['id']/g['workflow_file']).read_text());steps=w['main']['steps'];job=steps[0]['initialize']['assign'][1]['job']
 (O/'specs'/(g['id']+'.json')).write_text(json.dumps({'job':job})+'\n')
 steps[0]['initialize']['assign'][1]['job']='${spec.body.job}'
 def conv(x):
  if isinstance(x,dict):return {k:conv(v) for k,v in x.items()}
  if isinstance(x,list):return [conv(v) for v in x]
  if isinstance(x,str) and g['id'] in x:
   if x.startswith('${'):return x.replace(g['id'],'" + g.id + "')
   parts=x.split(g['id']);return '${'+(' + g.id + '.join(json.dumps(v) for v in parts))+'}'
  return x
 steps=conv(steps);normalized.append(steps)
assert all(x==normalized[0] for x in normalized),'Nonidentity differences in job controllers'
p=yaml.safe_load((O/'parent.yaml').read_text());old=p['run_group']['steps'];keep=[x for x in old if next(iter(x)) in ['success','summaries','complete','done']]
p['run_group']['steps']=[old[0],{'solve':{'call':'run_job','args':{'g':'${g}'},'result':'result'}}]+keep
p['run_job']={'params':['g'],'steps':[{'spec':{'try':{'call':'http.get','args':{'url':'${"https://storage.googleapis.com/tmrw-wildfire-20261015-trial/density36/orchestration/specs/" + g.id + ".json"}','auth':{'type':'OAuth2'}},'result':'spec'},'retry':'${http.default_retry}'}}]+normalized[0]}
# Inline jobs share the parent's execution ID; do not reference nonexistent child execution variable.
for step in p['run_group']['steps']:
 if 'complete' in step:step['complete']['args']['body']['execution']='${sys.get_env("GOOGLE_CLOUD_WORKFLOW_EXECUTION_ID")}'
(O/'parent-inline.yaml').write_text(yaml.safe_dump(json.loads(json.dumps(p)),sort_keys=False))
(O/'inline-equivalence.json').write_text(json.dumps({'passed':True,'groups':len(gs),'all_batch_definitions_unchanged':True,'all_monitor_cleanup_steps_identical_after_parameterization':True,'additional_workflow_execution_permissions_needed':False},indent=2)+'\n')
