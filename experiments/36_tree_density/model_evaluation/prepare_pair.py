"""Prepare the authorized matched single-split stride-one pair; no fitting."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data/model-pair';OLD=R.parent/'35_surrogate_diagnostics'
def main():
 (D/'data').mkdir(parents=True,exist_ok=True)
 a=np.load(R/'data/learning/sequences.npz');s=a['state'];t=a['time'];q=np.maximum(s[:,:,2],0);dt=np.diff(t);cum=np.c_[np.zeros(len(s)),np.cumsum((q[:,1:]+q[:,:-1])*.5*dt,1)];j=np.arange(1,91);k=np.maximum(j-5,0);elapsed=t[:,j]-t[:,k]
 water=np.maximum(s[:,k,0]-s[:,j,0],0)/s[:,0,0,None]/elapsed;dry=np.maximum(s[:,k,1]-s[:,j,1],0)/s[:,0,1,None]/elapsed;gas=(cum[:,j]-cum[:,k])/.75/s[:,0,1,None]/elapsed
 rates=np.stack([water,dry,gas],-1).astype('float32');data={n:a[n] for n in a.files};data.update(gate_rates=rates,gate_targets=(rates>=1e-4).astype('float32'),gate_supervised=((rates<1e-5)|(rates>=1e-4)))
 old=np.load(OLD/'attempt24/data/sequences.npz')
 for key in ('gate_rates','gate_targets','gate_supervised'):assert np.array_equal(data[key][:520],old[key]),key
 np.savez_compressed(D/'data/sequences.npz',**data)
 meta=json.loads((R/'learning-schema.json').read_text());meta['rotations']=meta['rotations'][:1];meta.update(comparison='Matched plain and soft-gated four-state GRUs, stride-one curriculum, rotation0',scope='Single fixed grouped8/1/1 split; generic cones; no physical validation')
 shutil.copyfile(R/'model_evaluation/time_pair.py',D/'time_cloud.py')
 (D/'schema.json').write_text(json.dumps(meta,indent=2)+'\n')
 shutil.copyfile(OLD/'attempt25/model.py',D/'plain_model.py');shutil.copyfile(OLD/'attempt24/model.py',D/'gated_model.py')
 (D/'model.py').write_text("from plain_model import Transition as Plain, normalize_fit\nfrom gated_model import Transition as Gated\ndef Transition(kind='control'):\n assert kind in ('control','gated')\n return Plain(kind) if kind=='control' else Gated(kind)\n")
 source=(R/'data/model-training/worker.py').read_text()
 def replace(a,b):
  nonlocal source
  assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
 replace("import torch\n","import torch\nimport torch.nn.functional as F\n")
 replace("activity_labels=torch.tensor(a['activity_labels'],device=device)","activity_labels=torch.tensor(a['activity_labels'],device=device)\ngate_targets=torch.tensor(a['gate_targets'],device=device);gate_supervised=torch.tensor(a['gate_supervised'],device=device)")
 replace("len(meta['rotations'])==10","len(meta['rotations'])==1")
 replace('range(0,90,h)','range(0,91-h)')
 replace('    loss+=(state_loss*weights',"    if kind=='gated':\n     supervised=gate_supervised[ids,jj];bce=F.binary_cross_entropy_with_logits(model.last_gate_logits,gate_targets[ids,jj],reduction='none');state_loss+=P['gate_loss_weight']*(bce*supervised).sum(-1)/supervised.sum(-1).clamp_min(1)\n    loss+=(state_loss*weights")
 replace('assert len(reports)==10','assert len(reports)==2')
 replace('folds=10))','folds=2))')
 replace('Plain four-state GRU on2080 histories: ten grouped8/1/1 rotations; frozen scorecard-v1; previously examined reshuffled data, not pristine. More histories change optimizer updates per epoch; not compute-matched.','Plain and soft-gated four-state GRUs on one fixed grouped8/1/1 split, stride-one full windows at every curriculum stage; both selections before tests. Previously examined data; not ten-fold aggregate. Overlap changes optimizer updates and transition exposure.')
 compile(source,'pair-worker','exec');(D/'worker.py').write_text(source)
 p=json.loads((R/'data/model-training/coverage-plan.json').read_text());p.update(experiment='Density36 matched single-split stride-one plain/gated pair',arms=['control','gated'],gate_loss_weight=.1,selection='Both validation selections frozen before either test',test='Shared rotation0 test fold, 208 histories',budget={'soft_seconds':72000,'maximum_allowance_usd':17.6})
 (D/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
 (D/'runtime.py').write_text((R/'data/model-training/runtime.py').read_text().replace('model-training01/','model-pair-preflight01/'))
 rot=meta['rotations'][0];sets=[set(rot[k]) for k in ('train','validation','test')];assert set.union(*sets)==set(range(2080));assert all(sets[i].isdisjoint(sets[j]) for i,j in ((0,1),(0,2),(1,2)))
 groups=[set(a['configuration'][sorted(x)]) for x in sets];assert list(map(len,groups))==[1632,204,204];assert all(groups[i].isdisjoint(groups[j]) for i,j in ((0,1),(0,2),(1,2)))
 proof=dict(prepared=True,launched=False,rotation=0,train_histories=len(rot['train']),validation_histories=len(rot['validation']),test_histories=len(rot['test']),old_gate_labels_bitwise=True,windows_per_history={str(h):len(range(0,91-h)) for h in (1,8,16,32)},plain_model_sha256=hashlib.sha256((D/'plain_model.py').read_bytes()).hexdigest(),gated_model_sha256=hashlib.sha256((D/'gated_model.py').read_bytes()).hexdigest(),selection_barrier_models=2,gate_loss_weight=.1,notes=['Original model implementations byte-identical; factory chooses correct class.','Gated gas initially multiplied by sigmoid(4), approximately0.982, unlike exact plain persistence.','Three soft gates affect water/fuel increments and gas release; heating ungated; no hard physical constraints.','Overlapping windows retain existing weights and repeat interior transitions; optimizer work increases.'])
 (R/'results/model-pair-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
