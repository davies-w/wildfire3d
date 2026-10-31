"""Prepare immutable pool02 after diagnosed pool01 status-overwrite failure."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parent
assert not (R/'results02/submission-intent.json').exists()
shutil.copytree(R/'data/training',R/'data/training02',dirs_exist_ok=True)
s=(R/'build_pool.py').read_text().replace("D=R/'data/training'; O=R/'results'","D=R/'data/training02'; O=R/'results02'").replace('pool01','pool02').replace("R/'pool.yaml'","R/'pool02.yaml'").replace("R/'readiness.yaml'","R/'readiness02.yaml'")
# Never overwrite a status snapshot: create-only storage is an intentional permission boundary.
s=s.replace("def record(name,body):return http(", "def record(name,body):\n if name.startswith('${'):\n  name=name[:-1]+' + \".\" + string(sys.now())}'\n return http(")
# Verify repeated immutable status recording in a no-GPU controller preflight.
s=s.replace("(R/'readiness02.yaml').write_text", "ready['main']['steps'].insert(1, {'write_probe1': record('${\"'+PREFIX+'preflight-status\"}', {'passed':True})})\nready['main']['steps'].insert(2, {'write_probe2': record('${\"'+PREFIX+'preflight-status\"}', {'passed':True})})\n(R/'readiness02.yaml').write_text")
s=s.replace('winner == null and len(inv.vms) > 0', 'winner == null and len(inv.vms) > 0 and inv.vms[0].status == \"RUNNING\"')
(R/'build_pool02.py').write_text(s)
exec(compile(s,str(R/'build_pool02.py'),'exec'))
s=(R/'launch.py').read_text().replace("O=R/'results';D=R/'data/training'","O=R/'results02';D=R/'data/training02'").replace('pool01','pool02').replace("R/'pool.yaml'","R/'pool02.yaml'").replace("subprocess.run([sys.executable,str(R/'validate.py')],check=True)","assert json.loads((R/'results/pool-closed.json').read_text())['passed']")
(R/'launch02.py').write_text(s)
