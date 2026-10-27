"""TRAIN replica comparison of physical and asinh-space gas averages; no fitting."""
from pathlib import Path
import json
import numpy as np
R=Path(__file__).resolve().parents[1]
a=np.load(R/'data/pair-sequence/rotation0/data/sequences.npz')
m=json.loads((R/'data/pair-sequence/rotation0/schema.json').read_text())
ids=np.array(m['rotations'][0]['train']);config=a['configuration'];scale=m['physical_encoding_scales'][2];grid=np.arange(0,181,2);rows=[]
for c in np.unique(config[ids]):
 group=ids[config[ids]==c]
 if len(group)<2:continue
 gas=np.array([np.interp(grid,a['time'][i],a['state'][i,:,2]) for i in group]);assert (gas>=0).all()
 encoded=np.arcsinh(gas/scale);n=len(group);physical=(gas.sum(0)[None]-gas)/(n-1);transformed=np.sinh((encoded.sum(0)[None]-encoded)/(n-1))*scale
 assert (transformed<=physical+1e-10).all()
 peak=gas.max(1);denom=np.maximum(peak,1e-30)
 def deficit(pred):return (np.maximum(gas[:,:17]-pred[:,:17],0).max(1)/denom).tolist()
 rows.append(dict(configuration=int(c),replicas=n,physical_mean_startup_deficit=deficit(physical),encoded_mean_startup_deficit=deficit(transformed),max_extra_startup_amplitude_suppression_fraction_of_true_peak=((physical[:,:17]-transformed[:,:17]).max(1)/denom).tolist()))
def summary(key):
 v=[x for r in rows for x in r[key]]
 return dict(median=float(np.median(v)),p90=float(np.quantile(v,.9)),maximum=float(np.max(v)))
out=dict(train_only=True,optimizer_updates=0,replicated_configurations=len(rows),histories=sum(r['replicas'] for r in rows),gas_encoding_scale_kg_s=scale,physical_mean=summary('physical_mean_startup_deficit'),encoded_mean=summary('encoded_mean_startup_deficit'),extra_suppression=summary('max_extra_startup_amplitude_suppression_fraction_of_true_peak'),scope='Leave-one-replica-out averages of other TRAIN seeds at matched nominal2s times, interpolated from actual timestamps. Encoded mean minimizes sample asinh-space squared error, physical mean minimizes sample physical squared error. Affine normalization cancels in the mean. Not a model forecast, causal isolation of actual training, irreducible error floor, or evidence about unreplicated configurations; only15 replicated training configurations. No validation/test use.',cases=rows)
(R/'results/gas-transform-bias-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2))
