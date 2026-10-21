"""Package cloud training input and bounded L4 workflow; does not submit or grant access."""
from pathlib import Path
import json,tarfile,hashlib,io,yaml,base64
R=Path(__file__).parent;S=R.parent/'31_tree_variations'
def main():
 assert json.loads((R/'results/learning-interface-check.json').read_text())['passed']
 names=['evaluation-plan.json','learning_worker.py','geometry_model.py','sequence.py','original_cnn.py','previous_loss.py','snapshot_evaluation.py','fresh-tests.json','groups.json','preprocess_cloud.py','fields.py','material_reader.py','fortran_records.py','data/geometries.npz','data/models/sequence_stage1.pt','data/models/previous.pt']
 files={n:R/n for n in names};files['cases.json']=R/'development.json';cs=json.loads((R/'development.json').read_text())
 for c in cs:
  if c['case'].startswith('x32_'):continue
  n='data/'+c['case']+'-material.npz';files[n]=R/n
  if c['case'].startswith('v31_'):
   for suffix in ['.npy','-time.npy']:n='data/fields/'+c['case']+suffix;files[n]=R/n
 hashes={}
 with tarfile.open(R/'data/learning-overlay.tar','w') as tar:
  for n,p in files.items():
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
   hashes[n]=h.hexdigest();tar.add(p,arcname=n)
  raw=json.dumps(hashes,indent=2).encode();ti=tarfile.TarInfo('learning-hashes.json');ti.size=len(raw);tar.addfile(ti,io.BytesIO(raw))
 (R/'results/learning-input-freeze.json').write_text(json.dumps(hashes,indent=2))
 w=yaml.safe_load((S/'gpu-workflow.yaml').read_text());a=w['main']['steps'][0]['initialize']['assign'];a[0]['deadline']='${sys.now() + 10800}';task=a[1]['job']['taskGroups'][0]['taskSpec'];task['maxRunDuration']='8400s';a[1]['job']['allocationPolicy']['instances'][0]['policy']['bootDisk']['sizeGb']='200'
 cmd=task['runnables'][0]['container']['commands'][1];encoded=cmd.split("base64.b64decode('",1)[1].split("')",1)[0];source=base64.b64decode(encoded).decode().replace('variation31/gpu01/learning-overlay.tar','expansion32/gpu01/learning-overlay.tar')
 source=source.replace("sys.path.insert(0,str(p));runpy.run_path", "(p/'transfer.tar').unlink();sys.path.insert(0,str(p));runpy.run_path(str(p/'preprocess_cloud.py'),run_name='__main__');runpy.run_path")
 compile(source,'bootstrap','exec');task['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+"),'bootstrap','exec'))"]
 raw=json.dumps(w).replace('gpu31-learning01','gpu32-learning01').replace('variation31/gpu01/job-status.json','expansion32/gpu01/job-status.json').replace('+ 2100','+ 9000')
 (R/'gpu-workflow.yaml').write_text(yaml.safe_dump(json.loads(raw),sort_keys=False));print('Prepared training overlay bytes',(R/'data/learning-overlay.tar').stat().st_size)
if __name__=='__main__':main()
