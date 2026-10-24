"""Freeze approved states and conditions without fitting any model."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent
meta=json.loads((R/'schema.json').read_text());a=np.load(R/'data/candidates.npz')
x=a['state'].astype('float32');t=a['time'].astype('float32')
# Initial masses encode initial water/fuel loading, not later targets.
g=np.concatenate([a['conditions'],x[:,0,:2]],-1).astype('float32')
np.savez_compressed(R/'data/sequences.npz',state=x,time=t,geometry=g,configuration=a['configuration'],fold=a['fold'])
meta.update(status='approved and frozen',state_names=meta['candidate_state_names'],physical_encoding_scales=[1,1,.01],external_names=meta['conditions']+['initial_water_kg','initial_unreacted_fuel_kg','ignition_on_fraction','dt_s'],external_scales=[10,1,5,1,1,10,10,1,2],history_steps=4,model_input_shape=['batch',21],model_output_shape=['batch',3],histories=520,configurations=480,transitions=46800)
(R/'schema.json').write_text(json.dumps(meta,indent=2))
(R/'results/data-verification.json').write_text(json.dumps(dict(shape=list(x.shape),histories=520,transitions=46800,third_state='vegetation fuel-gas release kg/s, not heat',negative_water_min=float(x[:,:,0].min()),negative_dry_min=float(x[:,:,1].min()),finite=bool(np.isfinite(x).all())),indent=2))
