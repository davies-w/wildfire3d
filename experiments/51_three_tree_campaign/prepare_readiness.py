"""Add exact new API-read checks to the no-solver readiness workflow."""
from cloud import *
import yaml
class NoAlias(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
assert not (P/'submission-intent.json').exists()
p=R/'readiness.yaml';r=yaml.safe_load(p.read_text());w=yaml.safe_load((R/'workflow.yaml').read_text())
steps=r['main']['steps']
if not any('read_admission' in x for x in steps):
 additions=[w['main']['steps'][1],w['main']['steps'][2],w['main']['steps'][3]]
 additions.append({'task_list_access':{'try':{'call':'http.get','args':{'url':'https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/jobs/'+WF+'-access-check/taskGroups/group0/tasks','auth':{'type':'OAuth2'},'query':{'pageSize':1}}},'except':{'as':'e','steps':[{'expected_missing':{'switch':[{'condition':'${map.get(e,"code") != 404}','raise':'${e}'}]}}]}}})
 steps[1:1]=additions
if not any('manifest_shape' in x for x in steps):
 index=next(i for i,x in enumerate(steps) if 'read_manifest' in x)
 steps.insert(index+1,{'manifest_shape':{'switch':[{'condition':'${len(manifest.body) != 111 or manifest.body[0].count != 6}','raise':'Unexpected frozen manifest shape'}]}})
temporary=p.with_suffix('.tmp');temporary.write_text(yaml.dump(r,Dumper=NoAlias,sort_keys=False));temporary.replace(p)
print('Readiness also verifies controller input reads and Batch task-list access')
