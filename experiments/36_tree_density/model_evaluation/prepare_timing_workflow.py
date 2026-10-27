"""Freeze a bounded cloud preflight package; never upload, grant, or execute."""
from pathlib import Path
import base64,hashlib,io,json,tarfile,yaml
R=Path(__file__).resolve().parents[1];D=R/'data/model-preflight';OLD=R.parent/'35_surrogate_diagnostics/attempt25'
def main():
 for name in ('preflight','evaluation-preflight','transport-preflight'):
  assert json.loads((D/'results'/f'{name}.json').read_text())['passed']
 frozen=json.loads((R/'results/model-preflight-inputs.json').read_text())['files']
 for name,digest in frozen.items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest
 dest=R/'data/model-timing';dest.mkdir(exist_ok=True)
 with tarfile.open(dest/'inputs.tar','w') as tar:
  for name in sorted(frozen):
   data=(D/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;tar.addfile(info,io.BytesIO(data))
  data=json.dumps(frozen,sort_keys=True).encode();info=tarfile.TarInfo('hashes.json');info.size=len(data);tar.addfile(info,io.BytesIO(data))
 w=yaml.safe_load((OLD/'gpu-workflow.yaml').read_text());job=w['main']['steps'][0]['initialize']['assign'][1]['job'];runnable=job['taskGroups'][0]['taskSpec']['runnables'][0]
 command=runnable['container']['commands'][1];encoded=command.split("b64decode('")[1].split("')")[0];source=base64.b64decode(encoded).decode()
 source=source.replace('diagnostics35/attempt25/pilot-overlay.tar','density36/model-preflight01/inputs.tar').replace('attempt25-upload-verification-probe','density36-preflight-upload-verification-probe').replace("p/'worker.py'","p/'time_cloud.py'")
 assert 'attempt25' not in source and "p/'time_cloud.py'" in source
 compile(source,'timing-bootstrap','exec')
 runnable['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+"),'bootstrap','exec'))"]
 raw=json.dumps(w).replace('gpu35-learning25','gpu36-preflight01').replace('diagnostics35/attempt25/job-status.json','density36/model-preflight01/job-status.json').replace('+ 12600','+ 2700').replace('+ 11100','+ 1200').replace('10800s','900s')
 w=json.loads(raw);assert w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['maxRetryCount']==0
 (dest/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False));(dest/'bootstrap.py').write_text(source)
 report={'submitted':False,'training':False,'workflow_id':'fds-gpu36-preflight01','private_prefix':'density36/model-preflight01/','input_sha256':hashlib.sha256((dest/'inputs.tar').read_bytes()).hexdigest(),'input_bytes':(dest/'inputs.tar').stat().st_size,'workflow_sha256':hashlib.sha256((dest/'workflow.yaml').read_bytes()).hexdigest(),'maximum_allowance_usd':.5,'funding':'Carve .50 from existing density36-learning $8 reservation before launch; do not double count','task_seconds':900,'vm_age_seconds':1200,'absolute_seconds':2700,'queue_seconds':1200,'automatic_retries':0,'scope':'One standard g2-standard-4 CUDA preflight/timing, no optimizer or test predictions. Bounded failure diagnostic only; full training is a separate frozen launch.'}
 (R/'results/model-timing-prepared.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
