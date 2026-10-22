import json
from scene import ROOT
out=[]
for name in ['b21_single_1','b21_transfer_hot']:
 r=json.loads((ROOT/'data/component_states'/f'{name}.json').read_text())
 for target in [1,2,5,10,15,20]:
  f=min(r['particle_frames'],key=lambda f:abs(f['time_s']-target));out.append(dict(case=name,time=f['time_s'],classes=f['canopies'][0]['classes']))
(ROOT/'results/component-hot-tail-diagnosis.json').write_text(json.dumps(out,indent=2))
