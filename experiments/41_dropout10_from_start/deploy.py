"""Deploy guarded controller and no-GPU readiness workflow; does not submit training."""
from pathlib import Path
import sys,subprocess,json
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'36_tree_density'))
from cloud import gc,G,PROJECT
assert not (R/'results/submission-intent.json').exists()
sa=gc('workflows','describe','fds-domain17','--location=us-central1')['serviceAccount']
for name,file in [('fds-gpu41-pool01','pool01.yaml'),('fds-gpu41-pool01-check','readiness01.yaml')]:
 subprocess.run([G,'workflows','deploy',name,'--project='+PROJECT,'--location=us-central1','--source='+str(R/file),'--service-account='+sa,'--format=json'],check=True)
print('Deployed controller/readiness; no training submitted')
