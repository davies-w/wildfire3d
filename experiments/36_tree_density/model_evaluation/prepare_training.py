"""Freeze the unchanged ten-fold recipe after GPU equivalence and runtime preflight."""
from pathlib import Path
import base64,hashlib,io,json,shutil,tarfile,yaml
R=Path(__file__).resolve().parents[1]
def main():
 for f in ['dataset-completeness','model-data-preflight','model-timing03-collected']:
  d=json.loads((R/'results'/f'{f}.json').read_text());assert d.get('passed',d.get('complete',False)),f
 t=json.loads((R/'results/model-training-runtime-plan03.json').read_text());assert t['projections']['400']['hours']<7
 assert json.loads((R/'data/model-timing03-results/report-equivalence.json').read_text())['passed']
 src=R/'data/model-preflight03';dst=R/'data/model-training';dst.mkdir(exist_ok=True);(dst/'data').mkdir(exist_ok=True)
 names=['worker.py','model.py','runtime.py','schema.json','data/sequences.npz','coverage-plan.json']
 for n in names:shutil.copyfile(src/n,dst/n)
 assert (dst/'worker.py').read_bytes()==(R/'data/model-report-candidate/worker.py').read_bytes()
 assert (dst/'model.py').read_bytes()==(R.parent/'35_surrogate_diagnostics/attempt25/model.py').read_bytes()
 (dst/'runtime.py').write_text((src/'runtime.py').read_text().replace('model-preflight03/','model-training01/'))
 p=json.loads((dst/'coverage-plan.json').read_text());p.update(experiment='Density36 frozen ten-fold plain four-state GRU',selection='All ten validation selections frozen before any test',test='One frozen grouped test partition per rotation; previously examined reshuffled data, not pristine',save_forecasts=True,budget={'soft_seconds':25200,'maximum_allowance_usd':6.5})
 (dst/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
 hashes={n:hashlib.sha256((dst/n).read_bytes()).hexdigest() for n in names}
 with tarfile.open(dst/'inputs.tar','w') as tar:
  for n in names:
   data=(dst/n).read_bytes();i=tarfile.TarInfo(n);i.size=len(data);tar.addfile(i,io.BytesIO(data))
  data=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(data);tar.addfile(i,io.BytesIO(data))
 bootstrap=(R/'data/model-timing03/bootstrap.py').read_text().replace('model-preflight03/','model-training01/').replace("p/'time_cloud.py'","p/'worker.py'")
 w=json.loads(json.dumps(yaml.safe_load((R/'data/model-timing03/workflow.yaml').read_text())).replace('gpu36-preflight03','gpu36-training01').replace('model-preflight03/','model-training01/').replace('+ 2700','+ 30600').replace('+ 1200}', '+ 28800}').replace('900s','27900s'))
 # Preserve the independent twenty-minute allocation queue deadline.
 for step in w['main']['steps']:
  if 'queue_deadline' in json.dumps(step) and 'assign' in str(step):
   for v in step.values():
    if isinstance(v,dict):
     for a in v.get('assign',[]):
      if 'queue_deadline' in a:a['queue_deadline']='${sys.now() + 1200}'
 w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(bootstrap.encode()).decode())+"),'bootstrap','exec'))"]
 (dst/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(dst/'bootstrap.py').write_text(bootstrap)
 r=dict(submitted=False,training=True,workflow_id='fds-gpu36-training01',input_sha256=hashlib.sha256((dst/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(dst/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((dst/'workflow.yaml').read_bytes()).hexdigest(),files=hashes,maximum_allowance_usd=6.5,soft_seconds=25200,task_seconds=27900,vm_age_seconds=28800,absolute_seconds=30600,queue_seconds=1200,rate_ceiling_usd_per_hour=.80,maximum_vm_cost_at_ceiling=6.4,checkpoint_policy='Every completed epoch retains model, optimizer, RNG, history and best state; first epoch validates nonempty optimizer replay. Deadline checkpoint; no automatic continuation.',reporting_difference='Equal configuration weighting with changed floating reduction order; GPU equivalence rtol1e-5 atol1e-7, deterministic replay passed.',no_test_before_all_ten_selections=True)
 (R/'results/model-training-prepared.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
