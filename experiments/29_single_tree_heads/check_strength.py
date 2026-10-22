import json,torch,numpy as np
from models import Strength
from original_cnn import ROOT
z=np.load(ROOT/'data/scalar_targets.npz');m=Strength();m.load_state_dict(torch.load(ROOT/'data/models/strength.pt',weights_only=True))
with torch.no_grad():p=torch.expm1(m(torch.from_numpy(z['x']))).numpy()
y=np.expm1(z['logq']);a={}
for split in ['train','validation']:
 sel=z['split']==split;late=sel&(z['x'][:,3]>=120/180);a[split]={'pooled_HRR_curve_relative_L1':float(abs(p[sel]-y[sel]).sum()/y[sel].sum()),'late_predicted_mean_kW':float(p[late].mean()),'late_FDS_mean_kW':float(y[late].mean())}
(ROOT/'results/strength-check.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
