"""Offline invariants plus no-GPU execution of actual budget/selection control flow."""
from pathlib import Path
import json,copy,yaml,hashlib,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,gc,save
D=R/'data/flex-queue';WF='fds-gpu36-flex-queue01-gate-check'
def main():
 w=yaml.safe_load((D/'workflow.yaml').read_text());p=json.loads((R/'results/flex-queue-prepared.json').read_text());source=R/'data/pair-sequence/rotation1';proof=[]
 for pkg in p['packages']:
  t=D/f"rotation{pkg['rotation']}";assert hashlib.sha256((t/'inputs.tar').read_bytes()).hexdigest()==pkg['sha256']
  for n in ['worker.py','model.py','plain_model.py','gated_model.py','check_resume.py','data/sequences.npz']:assert (t/n).read_bytes()==(source/n).read_bytes()
  plan=json.loads((t/'coverage-plan.json').read_text());old=json.loads((source/'coverage-plan.json').read_text())
  for key in ('experiment','test'):plan.pop(key);old.pop(key)
  assert plan==old
  schema=json.loads((t/'schema.json').read_text());rot=schema['rotations'][0];assert rot==json.loads((R/'learning-schema.json').read_text())['rotations'][pkg['rotation']]
  proof.append(pkg['rotation'])
 # Replace only external effects and GPU runner in a copy. Actual for-loop, budget gate,
 # completion decode, selection barrier, accounting and exits are evaluated by Workflows.
 def fixture(cost,fail=False):
  x=copy.deepcopy(w);x.pop('list_resources');x['run_pair']={'params':['job','job_id','label','prefix'],'steps':[{'done':{'return':{'final_state':'SUCCEEDED','cost_bound_usd':cost}}}]}
  def replace(v):
   if isinstance(v,list):return [replace(i) for i in v]
   if not isinstance(v,dict):return v
   if str(v.get('call','')).startswith('http.'):
    if v['call']=='http.get':
     freeze='selection-freeze' in v['args']['url'];body={'selected':[] if fail else [{},{}],'test_not_evaluated_yet':True} if freeze else {'success':True,'folds':2}
     return {'assign':[{v['result']:{'body':json.dumps(body)}}]}
    return {'assign':[{'last_fixture_write':True}]}
   return {k:replace(i) for k,i in v.items()}
  return replace(x)
 sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];runs=[]
 for name,cost,fail,expected in [('all',2.9,False,9),('budget',14.9,False,2),('barrier',2.9,True,0)]:
  f=D/('fixture-'+name+'.yaml');f.write_text(yaml.safe_dump(fixture(cost,fail),sort_keys=False));gc('workflows','deploy',WF,'--location=us-central1','--source='+str(f),'--service-account='+sa);e=gc('workflows','execute',WF,'--location=us-central1');save('results/flex-fixture-'+name+'-execution.json',e)
  for _ in range(30):
   q=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1')
   if q['state']!='ACTIVE':break
   time.sleep(2)
  if fail:assert q['state']=='FAILED' and 'Pair completion/selection barrier invalid' in json.dumps(q),q
  else:
   assert q['state']=='SUCCEEDED',q
   result=json.loads(q['result']);assert result['completed']==list(range(1,expected+1)) and result['spent_bound']<=40,result
  runs.append(q)
 save('results/flex-queue-checks.json',dict(passed=True,rotations_recipe_byte_unchanged=proof,cloud_no_gpu_fixtures=runs));print('All immutable recipe and cloud budget/selection gates PASS')
if __name__=='__main__':main()
