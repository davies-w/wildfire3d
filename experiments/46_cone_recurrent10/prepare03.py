"""Byte-identical checkpoint116 recovery after pre-training pool02 eviction."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
R=Path(__file__).resolve().parent;D=R/'data/training03';O=R/'results03'
assert not (O/'submission-intent.json').exists();assert json.loads((R/'results02/pool-closed.json').read_text())['passed']
O.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
p=json.loads((R/'results02/package.json').read_text())
for name,digest in p['files'].items():
 f=R/'data/training02'/name;assert hashlib.sha256(f.read_bytes()).hexdigest()==digest
 dst=D/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
subprocess.run([sys.executable,str(R/'build_pool03.py')],check=True)
q=json.loads((O/'package.json').read_text());assert q['files']==p['files'],'No scientific recipe or checkpoint changes permitted'
v=json.loads((R/'results02/continuation-validation.json').read_text());v['byte_identical_to_pool02']=True;(O/'continuation-validation.json').write_text(json.dumps(v,indent=2)+'\n')
print('All input file hashes identical; resume epoch117 unchanged')
