from pathlib import Path
import json,tarfile,hashlib,shutil
R=Path(__file__).parent;D=R/'data/gpu/cloud';done=json.loads((D/'complete.json').read_text());assert done['success'];assert hashlib.sha256((D/'outputs.tar').read_bytes()).hexdigest()==done['output_sha256'];assert not any(json.loads((R/'results/gpu-cleanup.json').read_text()).values())
folder=R/'data/gpu/adopted';folder.mkdir(exist_ok=True)
with tarfile.open(D/'outputs.tar') as t:t.extractall(folder,filter='data')
freeze=json.loads((folder/'results/prediction-freeze.json').read_text())
learning=json.loads((folder/'results/learning.json').read_text());assert learning['input_hashes']['learning']==json.loads((R/'results/learning-input-freeze.json').read_text());assert learning['input_hashes']['base']==json.loads((R.parent/'29_single_tree_heads/gpu_training/results/input-hashes.json').read_text())
for n,h in freeze['files'].items():
 src=folder/n;assert hashlib.sha256(src.read_bytes()).hexdigest()==h;dst=R/n
 if n.endswith('.py') or n=='fresh-tests.json':assert dst.read_bytes()==src.read_bytes(),n
 else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for n in ['results/learning.json','results/prediction-freeze.json']:shutil.copy2(folder/n,R/n)
print('Verified frozen models and predictions; fresh FDS tests may now launch')
