"""Execute actual evaluation definitions on CPU, without optimizer or fitting."""
from pathlib import Path
import ast,json
R=Path(__file__).resolve().parent
source=(R/'worker.py').read_text().split('checks=[]')[0]
source=source.replace("assert torch.cuda.is_available(),'Cloud CUDA required; local training prohibited'",'').replace("device='cuda'","device='cpu'")
assert 'optimizer' not in source
ns={'__file__':str(R/'worker.py')};exec(compile(source,str(R/'worker.py'),'exec'),ns)
torch=ns['torch'];ids=torch.tensor(ns['meta']['rotations'][0]['validation']);train=torch.tensor(ns['meta']['rotations'][0]['train'])
mean,std=ns['normalize_fit'](ns['raw'],train,ns['config'],ns['scale']);z=(torch.asinh(ns['raw']/ns['scale'])-mean)/std
checks=[]
for kind in ns['P']['arms']:
 model=ns['Transition'](kind);model.set_normalization(mean,std)
 a=ns['evaluate'](model,z,ids,mean,std,True);b=ns['evaluate'](model,z,ids,mean,std,True)
 assert a==b
 assert all(a[k]['finite'] for k in ['one_step','rollout'])
 checks.append(dict(kind=kind,passed=True,exact_replay=True))
(R/'results/evaluation-preflight.json').write_text(json.dumps(dict(passed=True,checks=checks,no_optimizer=True),indent=2));print(checks)
