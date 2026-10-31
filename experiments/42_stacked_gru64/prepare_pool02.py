"""Unique repaired pool after terminal pool01 audit; never mutate submitted inputs."""
from pathlib import Path
import json,shutil,subprocess,sys
R=Path(__file__).resolve().parent;D=R/'data/training02';O=R/'results02'
assert json.loads((R/'results/pool-closed.json').read_text())['passed']
assert json.loads((R/'results/failure-audit.json').read_text())['no_completed_epochs']
assert not (O/'submission-intent.json').exists()
O.mkdir(exist_ok=True);shutil.copytree(R/'data/training',D,dirs_exist_ok=True)
shutil.copy2(R/'gated_model02.py',D/'gated_model.py')
for stale in ['inputs.tar','hashes.json','bootstrap.py']:(D/stale).unlink(missing_ok=True)
subprocess.run([sys.executable,str(R/'build_pool02.py')],check=True)
