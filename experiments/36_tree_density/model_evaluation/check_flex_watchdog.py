"""Exercise actual watchdog flow with external actions replaced by no-GPU fixtures."""
import sys,json,copy,time,yaml
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import R,gc,save
D=R/'data/flex-queue';WF='fds-gpu36-flex-watchdog-check'
w=yaml.safe_load((D/'workflow.yaml').read_text());sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount'];runs=[]
for present in (True,False):
 child=copy.deepcopy(w['run_pair'])
 def replace(v):
  if isinstance(v,list):return [replace(x) for x in v]
  if not isinstance(v,dict):return v
  if v.get('call')=='list_resources':
   value=[{'creationTimestamp':'${time.format(sys.now() - 3600)}','selfLink':'https://example.invalid/never-called'}] if v['result']=='active_vms' and present else []
   return {'assign':[{v['result']:value}]}
  if str(v.get('call','')).startswith('http.'):
   result=v.get('result')
   if result=='status':return {'assign':[{'status':{'body':{'status':{'state':'SUCCEEDED'}}}}]}
   if result=='created':return {'assign':[{'created':{'body':{'uid':'fixture'}}}]}
   return {'assign':[{'fixture_no_network_action':True}]}
  if v.get('call')=='sys.sleep':return {'assign':[{'fixture_sleep_skipped':True}],**({'next':v['next']} if 'next'in v else {})}
  return {k:replace(x) for k,x in v.items()}
 child=replace(child);fixture={'main':{'steps':[{'run':{'call':'run_pair','args':{'job':{},'job_id':'fixture','label':'fixture','prefix':'fixture/'},'result':'r'}},{'done':{'return':'${r}'}}]},'run_pair':child}
 f=D/('watchdog-fixture-'+str(present)+'.yaml');f.write_text(yaml.safe_dump(fixture,sort_keys=False));gc('workflows','deploy',WF,'--location=us-central1','--source='+str(f),'--service-account='+sa);e=gc('workflows','execute',WF,'--location=us-central1')
 for _ in range(30):
  q=gc('workflows','executions','describe',e['name'].split('/')[-1],'--workflow='+WF,'--location=us-central1')
  if q['state']!='ACTIVE':break
  time.sleep(2)
 assert q['state']=='SUCCEEDED',q
 r=json.loads(q['result']);assert r['final_state']=='SUCCEEDED' and (.9<=r['cost_bound_usd']<1 if present else r['cost_bound_usd']==15.2),r;runs.append(q)
save('results/flex-watchdog-checks.json',dict(passed=True,no_gpu=True,fixtures=runs));print('Watchdog VM-age/cleanup/accounting paths PASS')
