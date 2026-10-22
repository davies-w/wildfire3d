"""Fit on development evidence, choose epochs by validation, freeze all test predictions."""
import copy
import hashlib
import json
import time
import numpy as np
import torch
from models import ROOT,batch,model,loss

def train():
    frozen=ROOT/'results/frozen-weights.json'
    if frozen.exists():raise RuntimeError('Predictions already frozen; no automatic refit after test access')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    rows=json.loads((ROOT/'data/development.json').read_text())
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    assert len(train)>=24 and len(val)>=6
    assert {r['target'][0] for r in val}=={0,1},'Validation needs both classes overall'
    assert len({r['layout'] for r in train if r['target'][0]})>=3,'Need three positive training geometries'
    assert all(len(r['layout'])<=2 for r in rows),'Development must contain only one/two crowns'
    assert all(r.get('duration_s',30) in (10,20,30) for r in rows),'Unsupported source duration'
    assert len([r for r in train if r.get('duration_s',30)==20])>=12,'Need matched-duration training coverage'
    assert len({r['layout'] for r in train if r.get('duration_s',30)==20 and r['target'][0]})>=3,'Need three positive 20-second training geometries'
    assert not ({r['layout'] for r in train}&{r['layout'] for r in val}),'Hold validation geometries out of training'
    assert {r['target'][0] for r in train}=={0,1},'Training labels lack both classes; inconclusive pilot'
    cfg=json.loads((ROOT/'training.json').read_text())
    ft=batch(train);fv=batch(val)
    yt=torch.tensor([r['target'] for r in train]);yv=torch.tensor([r['target'] for r in val])
    at=torch.tensor([r['auxiliary'] for r in train]);av=torch.tensor([r['auxiliary'] for r in val])
    outputs=[];models_dir=ROOT/'data/models';models_dir.mkdir(exist_ok=True)
    for kind in ('graph','additive','simple','ignition_only'):
        for seed in cfg['seeds']:
            torch.manual_seed(seed);m=model(kind)
            optimizer=torch.optim.AdamW(m.parameters(),lr=cfg['learning_rate'],weight_decay=cfg['weight_decay'])
            best=float('inf');best_state=None;best_epoch=0;curve=[]
            for epoch in range(1,cfg['epochs']+1):
                m.train();optimizer.zero_grad();value=loss(m(*ft),yt,at);value.backward()
                torch.nn.utils.clip_grad_norm_(m.parameters(),5);optimizer.step()
                if epoch%10:continue
                m.eval()
                with torch.no_grad():
                    pred=torch.sigmoid(m(*fv)[0][:,0]);score=float(torch.stack([((pred[mask]-yv[mask,0])**2).mean() for label in (0,1) for mask in [yv[:,0]==label]]).mean())
                    training_brier=float(((torch.sigmoid(m(*ft)[0][:,0])-yt[:,0])**2).mean())
                curve.append(dict(epoch=epoch,train_loss=float(value.detach()),train_brier=training_brier,validation_brier=score))
                if score<best:
                    best=score;best_epoch=epoch;best_state=copy.deepcopy(m.state_dict())
            m.load_state_dict(best_state);m.eval()
            torch.save(best_state,models_dir/f'{kind}_{seed}.pt')
            checkpoint=models_dir/f'{kind}_{seed}.pt'
            outputs.append(dict(kind=kind,seed=seed,best_epoch=best_epoch,validation_brier=best,
                parameters=sum(p.numel() for p in m.parameters()),curve=curve,
                checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest()))
            print(kind,seed,'selected epoch',best_epoch,'validation Brier',round(best,4),flush=True)
    payload=dict(created_unix=time.time(),test_labels_read=False,torch_version=torch.__version__,
        hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('training.json','models.py','train.py','design.json','data/development.json')},
        models=outputs)
    frozen.write_text(json.dumps(payload,indent=2)+'\n')
    print('Frozen weights; confirmation inputs and outcomes have not been read.')
if __name__=='__main__':train()
