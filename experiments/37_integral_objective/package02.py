from pathlib import Path
import hashlib,json,tarfile,base64,yaml,shutil
R=Path(__file__).resolve().parent;D=R/'data/training02';OLD=R.parent/'36_tree_density/data/canonical-pilot03'
shutil.copy2(R/'cloud_check02.py',D/'cloud_check.py')
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.npz') and p.name not in ['hashes.json'] and 'results' not in p.parts}
(D/'hashes.json').write_text(json.dumps(files,indent=2))
with tarfile.open(D/'inputs.tar','w') as tar:
 for n in sorted([*files,'hashes.json']):tar.add(D/n,arcname=n)
digest=hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()
boot=(OLD/'bootstrap.py').read_text().replace('density36/canonical-pilot03/','integral37/training02/')
boot=boot.replace("with tarfile.open(p/'transfer.tar') as tar:","assert hashlib.sha256((p/'transfer.tar').read_bytes()).hexdigest()=="+repr(digest)+"\nwith tarfile.open(p/'transfer.tar') as tar:")
boot=boot.replace("runpy.run_path(str(p/'worker.py'),run_name='__main__')","import subprocess\n subprocess.run([sys.executable,str(p/'cloud_check.py')],check=True,timeout=900)\n runpy.run_path(str(p/'worker.py'),run_name='__main__')")
(D/'bootstrap.py').write_text(boot)
w=(OLD/'workflow.yaml').read_text().replace('gpu36-canonical03','gpu37-integral02').replace('density36/canonical-pilot03/','integral37/training02/').replace('sys.now() + 3600','sys.now() + 61200').replace('2730s','58500s').replace('+ 2850','+ 59400')
x=yaml.safe_load(w);x['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode('"+base64.b64encode(boot.encode()).decode()+"'),'bootstrap','exec'))"]
(D/'workflow.yaml').write_text(yaml.safe_dump(x,sort_keys=False))
proof=dict(files=files,input_sha256=digest,input_bytes=(D/'inputs.tar').stat().st_size,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),maximum_allowance_usd=20.8,soft_seconds=57600,task_seconds=58500,vm_seconds=59400,absolute_seconds=61200,queue_seconds=900)
(R/'results02/package.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
