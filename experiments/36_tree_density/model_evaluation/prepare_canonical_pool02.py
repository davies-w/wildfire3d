"""Prepare an identical scientific trial with two supported allocation zones."""
from pathlib import Path
import base64,hashlib,io,json,shutil,tarfile,yaml
R=Path(__file__).resolve().parents[1];S=R/'data/canonical-pilot01';D=R/'data/canonical-pilot02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (R/'results/canonical-pilot02-execution.json').exists()
 old=json.loads((R/'results/canonical-pilot01-prepared.json').read_text())
 closed=json.loads((R/'results/canonical-pilot01-no-allocation-proof.json').read_text());assert closed['passed'] and closed['successful_vm_allocations']==0
 assert json.loads((R/'results/canonical-pilot01-permission-removed.json').read_text())['exact_grant_removed']
 D.mkdir(exist_ok=True)
 for n,h in old['files'].items():
  assert sha(S/n)==h,n
  shutil.copyfile(S/n,D/n)
 runtime=(D/'runtime.py').read_text();assert runtime.count('density36/canonical-pilot01/')>0;(D/'runtime.py').write_text(runtime.replace('density36/canonical-pilot01/','density36/canonical-pilot02/'))
 hashes={n:sha(D/n) for n in old['files']}
 assert [n for n in hashes if hashes[n]!=old['files'][n]]==['runtime.py']
 with tarfile.open(D/'inputs.tar','w') as tar:
  for name in hashes:
   b=(D/name).read_bytes();i=tarfile.TarInfo(name);i.size=len(b);tar.addfile(i,io.BytesIO(b))
  b=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(b);tar.addfile(i,io.BytesIO(b))
 bootstrap=(S/'bootstrap.py').read_text().replace('density36/canonical-pilot01/','density36/canonical-pilot02/');(D/'bootstrap.py').write_text(bootstrap)
 w=yaml.safe_load((S/'workflow.yaml').read_text().replace('gpu36-canonical01','gpu36-canonical02').replace('density36/canonical-pilot01/','density36/canonical-pilot02/'))
 steps=w['main']['steps'];job=steps[0]['initialize']['assign'][1]['job'];job['allocationPolicy']['location']['allowedLocations']=['zones/us-east4-a','zones/us-east4-c'];job['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 def both(step_name,body,result):
  # Every VM query and cleanup verification covers both allowed zones.
  a=json.loads(json.dumps(body));c=json.loads(json.dumps(body));a['args']['url']=a['args']['url'].replace('us-east4-c','us-east4-a');a['result']=result+'_a';c['result']=result+'_c'
  joined={'assign':[{result:{'body':{'items':'${default(map.get('+result+'_a.body, "items"), [])}'}}}]}
  append={'for':{'value':'pool_vm','in':'${default(map.get('+result+'_c.body, "items"), [])}','steps':[{step_name+'_append_vm':{'assign':[{result+'.body.items':'${list.concat('+result+'.body.items, pool_vm)}'}]}}]}}
  return [{step_name+'_a':a},{step_name+'_c':c},{step_name:joined},{step_name+'_append_c':append}]
 monitor=next(s['monitor'] for s in steps if 'monitor' in s)['try']['steps'];i=next(i for i,s in enumerate(monitor) if 'get_vm' in s);monitor[i:i+1]=both('get_vm',monitor[i]['get_vm'],'active_vms')
 for name,result in [('list_workers','workers'),('verify','remaining')]:
  i=next(i for i,s in enumerate(steps) if name in s);steps[i:i+1]=both(name,steps[i][name],result)
 delete=next(s['delete_stragglers'] for s in steps if 'delete_stragglers' in s)['for']['steps'][0]['delete_vm']['try'];delete['args']['url']='${vm.selfLink}'
 (D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
 out={**old,'input_sha256':sha(D/'inputs.tar'),'input_bytes':(D/'inputs.tar').stat().st_size,'workflow_sha256':sha(D/'workflow.yaml'),'files':hashes,'prefix':'density36/canonical-pilot02/','label':'gpu36-canonical02','capacity_only_change':True,'scientific_package_reference':'canonical-pilot01','allowed_zones':['us-east4-a','us-east4-c']}
 assert out['input_bytes']==old['input_bytes']
 (R/'results/canonical-pilot02-prepared.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='files'},indent=2))
if __name__=='__main__':main()
