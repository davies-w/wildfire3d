from pathlib import Path
import json,yaml,base64
R=Path(__file__).parent;S=R.parent/'30_tree_sequence'
w=yaml.safe_load((S/'workflow.yaml').read_text());a=w['main']['steps'][0]['initialize']['assign'];a[0]['deadline']='${sys.now() + 3300}';task=a[1]['job']['taskGroups'][0]['taskSpec'];cmd=task['runnables'][0]['container']['commands'][1]
# Decode the known, versioned bootstrap rather than reconstructing quoting.
encoded=cmd.split("base64.b64decode('",1)[1].split("')",1)[0];source=base64.b64decode(encoded).decode().replace('gpu30/sequence01/overlay.tar','variation31/gpu01/learning-overlay.tar').replace('overlay-hashes.json','learning-hashes.json').replace("p/'worker.py'","p/'learning_worker.py'");compile(source,'bootstrap','exec');task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+"),'bootstrap','exec'))"]
s=json.dumps(w).replace('gpu30-sequence01','gpu31-learning01').replace('gpu30/sequence01/job-status.json','variation31/gpu01/job-status.json');w=json.loads(s)
for step in w['main']['steps']:
 if 'delete_stragglers' in step:
  for item in step['delete_stragglers']['for']['steps']:
   if 'delete_vm' in item and 'try' not in item['delete_vm']:item['delete_vm']={'try':item['delete_vm'],'except':{'as':'cleanup_error','steps':[{'check_cleanup_error':{'switch':[{'condition':'${map.get(cleanup_error, "code") != 404}','steps':[{'rethrow_cleanup':{'raise':'${cleanup_error}'}}]}]}}]}}
(R/'gpu-workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));print('Prepared GPU controller')
