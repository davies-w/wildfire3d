"""Canonical stride-one endpoint loss over real forecast lengths; frozen inputs, fit gradients only."""
from pathlib import Path
import json
import numpy as np
import torch
from guard_matched_data import GuardMatchedData

HORIZONS=(1,4,8,16,45)

class CanonicalData(GuardMatchedData):
    def __init__(self,root,device='cpu',canonical_root=None):
        super().__init__(root,device)
        path=lambda name:Path(canonical_root)/name if canonical_root is not None else Path(root)/('canonical-'+name)
        assert np.array_equal(np.load(path('source-ids.npy')),self.source_ids)
        # Private copy-on-write mapping avoids copying the1GB cache on CPU; never mutate it.
        tensor=lambda value:torch.as_tensor(value,device=device)
        self.cx=tensor(np.load(path('features.npy'),mmap_mode='c'))
        self.cb=tensor(np.load(path('base-states.npy'),mmap_mode='c'))
        self.co=tensor(np.load(path('offsets.npy'))).long()
        self.cl=tensor(np.load(path('lengths.npy'))).long()
        assert self.cx.shape==(len(self.raw),3060,46) and self.cb.shape==(len(self.raw),3060,4)
        norm=json.loads(path('fit-normalization.json').read_text())
        self.canonical_norm={h:tensor(norm[str(h)]['physical_MAE']).clamp_min(1e-8) for h in HORIZONS}
        self.canonical_case_factor=len(self.roles['fit'])/len(torch.unique(self.config[self.roles['fit']]))

    def canonical_batch(self,model,ids,horizons,origins):
        assert bool(self.fit_allowed[ids].all()),'Only fit histories may create canonical gradients'
        assert ids.shape==horizons.shape==origins.shape and len(ids)>0
        assert bool(((horizons==1)|(horizons==4)|(horizons==8)|(horizons==16)|(horizons==45)).all())
        assert bool(((origins>=0)&(origins+horizons<=90)).all())
        predictions=[];truth=[];base=[];normalizers=[];cases=[];ordered_origins=[];ordered_horizons=[]
        for h in HORIZONS:
            use=horizons==h;n=ids[use];origin=origins[use]
            if not len(n):continue
            assert bool((self.cl[origin]>=h).all())
            columns=self.co[origin,None]+torch.arange(h,device=self.device)[None]
            slots=origin[:,None]+torch.arange(h+1,device=self.device)[None]
            # Decode exactly h real steps, never a padded45step surrogate.
            prediction=model(self.cx[n[:,None],columns],self.cb[n[:,None],columns],self.raw[n,origin],self.times[n[:,None],slots])
            predictions.append(prediction[:,-1]);truth.append(self.raw[n,origin+h]);base.append(self.cb[n,columns[:,-1]])
            normalizers.append(self.canonical_norm[h][None].expand(len(n),-1));cases.append(n);ordered_origins.append(origin);ordered_horizons.append(horizons[use])
        case=torch.cat(cases)
        return dict(prediction=torch.cat(predictions),truth=torch.cat(truth),base=torch.cat(base),normalizers=torch.cat(normalizers),replica_weight=self.replica[case],case=case,origin=torch.cat(ordered_origins),horizon=torch.cat(ordered_horizons))

    @torch.no_grad()
    def score_canonical(self,model,ids,no_change=False):
        from canonical_metrics import score_horizon
        if bool(self.confirmation[ids].any()):assert self.confirmation_open,'Confirmation closed until selection freezes'
        report={}
        for h in HORIZONS:
            origins=torch.arange(91-h,device=self.device);columns=self.co[origins,None]+torch.arange(h,device=self.device)[None];slots=origins[:,None]+torch.arange(h+1,device=self.device)[None];predictions=[]
            for chunk in ids.split(8):
                if no_change:pred=self.raw[chunk[:,None],origins[None]]
                elif model is None:pred=self.cb[chunk[:,None],columns[:,-1][None]]
                else:
                    count=len(chunk)*len(origins);x=self.cx[chunk[:,None,None],columns[None]];b=self.cb[chunk[:,None,None],columns[None]];initial=self.raw[chunk[:,None],origins[None]];times=self.times[chunk[:,None,None],slots[None]]
                    pred=model(x.reshape(count,h,46),b.reshape(count,h,4),initial.reshape(count,4),times.reshape(count,h+1))[:,-1].reshape(len(chunk),len(origins),4)
                predictions.append(pred)
            report[str(h)]=score_horizon(torch.cat(predictions),self.raw[ids],self.times[ids],self.config[ids],self.labels[ids],h)
        return report

    @torch.no_grad()
    def score(self,model,ids,no_change=False):
        report=super().score(model,ids,no_change);report['canonical']=self.score_canonical(model,ids,no_change);return report

def canonical_physical_loss(batch,case_factor):
    per_history=((batch['prediction']-batch['truth']).abs()/batch['normalizers']).mean(-1)
    # For uniform fit-history/horizon/valid-origin draws this is an unbiased
    # mean of per-configuration, per-horizon normalized endpoint MAE.
    return case_factor*(per_history*batch['replica_weight']).mean()
