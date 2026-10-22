"""Freeze autonomous predictions before any held-out job is submitted."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from build import ROOT
from model_data import geometry
from graph_model import ComponentGraph

def main():
 freeze=ROOT/'results/prediction-freeze.json';assert not freeze.exists(),'Never overwrite a test freeze'
 torch.set_num_threads(4);cases=[c for c in json.loads((ROOT/'cases.json').read_text()) if c['split'].endswith('test')]
 models={}
 for label,filename,independent in [('single_composed','single-only.pt',False),('pair_adapted','pair-adapted.pt',False),('independent_additive','single-only.pt',True)]:
  m=ComponentGraph();m.load_state_dict(torch.load(ROOT/'data/models'/filename,weights_only=True));m.eval();models[label]=(m,independent)
 out=ROOT/'data/predictions';out.mkdir(exist_ok=True);runtimes=[]
 for c in cases:
  d=geometry(c);schedule=[c['strength'] if t+1<c['duration'] else 0. for t in np.arange(0,180,2)]
  for label,(m,independent) in models.items():
   start=time.perf_counter()
   with torch.no_grad():state,heat,rate=(m.additive_rollout if independent else m.rollout)(**{k:d[k] for k in ['static','xyz','instance','heater_xyz']},schedule=schedule)
   arrays=[v.numpy() for v in [state,heat,rate]];assert all(np.isfinite(v).all() for v in arrays)
   np.savez_compressed(out/f"{c['case']}__{label}.npz",time=np.arange(0,182,2),state=arrays[0],heat=arrays[1],rate=arrays[2],indices=d['indices'],instance=d['instance'].numpy(),fuel=d['fuel'].numpy())
   runtimes.append(dict(case=c['case'],model=label,seconds=time.perf_counter()-start))
 files=list(out.glob('*.npz'))+list((ROOT/'data/models').glob('*'))+[ROOT/p for p in ['graph_model.py','model_data.py','train.py','freeze_predictions.py','evaluate.py','extract.py','build.py','cases.json','data/tree-templates.json','results/input-freeze.json']]+[ROOT/'decks'/f"{c['case']}.fds" for c in cases]
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 freeze.write_text(json.dumps(dict(created_unix=time.time(),cases=[c['case'] for c in cases],files=hashes,inference_timings=runtimes,criteria='Report familiar and C-transfer cases separately; compare all three models for regional temperature, remaining mass, incident radiation/convection and emitted fuel. No ignition classification. Only two transfer arrangements, one weak source; no full gas/flame-field or species validation.',test_outputs_accessed=False),indent=2))
 print('FROZEN',len(cases),'cases;',len(hashes),'hashes',flush=True)
if __name__=='__main__':main()
