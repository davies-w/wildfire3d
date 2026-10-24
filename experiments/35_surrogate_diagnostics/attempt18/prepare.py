"""Copy only SHA256-verified preserved inputs and resume states. No optimization."""
from pathlib import Path
import json,shutil,hashlib,torch
R=Path(__file__).resolve().parent;old=R.parent/'attempt16';dest=R/'data/resume';dest.mkdir(parents=True,exist_ok=True);(R/'results').mkdir(exist_ok=True)
inv=json.loads((old/'results/partial-inventory.json').read_text())['files'];proof={}
for name in ['schema.json','data/sequences.npz']:shutil.copyfile(old/name,R/name)
for k in range(15):
 for suffix in ['-report.json','-selected.pt']:
  name=f'fold{k:02}'+suffix;p=old/'data/collected'/name;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==inv[name]['sha256'];shutil.copyfile(p,dest/name);proof[name]=h
name='fold15-epoch373.pt';p=old/'data/collected'/name;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==inv[name]['sha256'];shutil.copyfile(p,dest/'fold15.pt');proof['fold15.pt']=h
c=torch.load(dest/'fold15.pt',map_location='cpu',weights_only=False);assert c['fold']==15 and c['epoch']==373 and c['kind']=='gru';assert c['schema_hash']==hashlib.sha256((R/'schema.json').read_bytes()).hexdigest();assert c['history'][-1]['epoch']==373
assert all(k in c for k in ['optimizer','rng','best_state','best_epoch','globalstep'])
assert not (old/'data/collected/selection-freeze.json').exists();assert not list((old/'data/collected').glob('*-test.json'))
(R/'results/resume-proof.json').write_text(json.dumps(dict(source=str(old),files=proof,model15_epoch=373,completed_models=15,optimizer_rng_selection_preserved=True,test_not_started=True,local_training=False),indent=2))
