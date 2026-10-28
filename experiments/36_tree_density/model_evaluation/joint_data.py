"""Frozen features and role guards shared by offline checks and the CUDA trial."""
from pathlib import Path
import json
import numpy as np
import torch
from joint_metrics import score_prediction,groups

class JointData:
    def __init__(self, root, device='cpu', rolling_root=None):
        root=Path(root);self.device=device
        self.plan=json.loads((root/'candidate-plan.json').read_text())
        norm=json.loads((root/'base-normalization.json').read_text())
        a=np.load(root/'features.npz')
        tensor=lambda value:torch.tensor(value,device=device)
        self.x=tensor(a['features']);self.base=tensor(a['base_states']);self.raw=tensor(a['truth']);self.times=tensor(a['time']);self.config=tensor(a['configuration']);self.labels=tensor(a['activity_labels']);self.source_ids=a['source_ids']
        rx_path=Path(rolling_root)/'features.npy' if rolling_root is not None else root/'rolling-features.npy';rb_path=Path(rolling_root)/'base-states.npy' if rolling_root is not None else root/'rolling-base-states.npy'
        self.rx=tensor(np.load(rx_path));self.rb=tensor(np.load(rb_path))
        self.scales=tensor(norm['physical_encoding_scales']);self.std=tensor(norm['std'])
        self.roles={name:torch.tensor(self.plan[name+'_indices'],device=device) for name in ['fit','selection','confirmation']}
        self.fit_allowed=torch.zeros(len(self.raw),device=device,dtype=torch.bool);self.fit_allowed[self.roles['fit']]=True
        self.confirmation=torch.zeros_like(self.fit_allowed);self.confirmation[self.roles['confirmation']]=True;self.confirmation_open=False
        self.replica=torch.zeros(len(self.raw),device=device);self.gas_peak=torch.zeros_like(self.replica)
        fit=self.plan['fit_indices'];config=a['configuration'];counts={int(c):int(np.count_nonzero(config[fit]==c)) for c in np.unique(config[fit])}
        self.replica[self.roles['fit']]=tensor([1/counts[int(config[i])] for i in fit]);self.gas_peak[self.roles['fit']]=self.raw[self.roles['fit'],:,2].abs().amax(1)
        for i,left in enumerate(self.roles):
            for right in list(self.roles)[i+1:]:assert not set(self.config[self.roles[left]].tolist())&set(self.config[self.roles[right]].tolist())

    def training_batch(self, model, ids, origins):
        assert bool(self.fit_allowed[ids].all()),'Only decoder-fit histories may create gradients'
        predictions=[];targets=[];initials=[];times=[];cases=[];valids=[]
        for full in [True,False]:
            use=origins<0 if full else origins>=0;n=ids[use]
            if not len(n):continue
            if full:
                t=self.times[n];initial=self.raw[n,0];truth=self.raw[n,1:];pred=model(self.x[n],self.base[n],initial,t);valid=torch.ones(len(n),90,device=self.device,dtype=torch.bool)
            else:
                origin=origins[use];slots=origin[:,None]+torch.arange(17,device=self.device)[None];t=self.times[n[:,None],slots];initial=self.raw[n,origin];truth=self.raw[n[:,None],slots[:,1:]];pred=model(self.rx[n,origin],self.rb[n,origin],initial,t)
                # Decode the real16steps first. Padding never enters the decoder.
                pred=torch.cat([pred,pred[:,-1:].expand(-1,74,-1)],1);truth=torch.cat([truth,truth[:,-1:].expand(-1,74,-1)],1);t=torch.cat([t,t[:,-1:]+2*torch.arange(1,75,device=self.device)[None]],1);valid=torch.arange(90,device=self.device)[None].expand(len(n),-1)<16
            predictions.append(pred);targets.append(truth);initials.append(initial);times.append(t);cases.append(n);valids.append(valid)
        pred=torch.cat(predictions);truth=torch.cat(targets);initial=torch.cat(initials);t=torch.cat(times);case=torch.cat(cases);valid=torch.cat(valids)
        prev=torch.cat([initial[:,None,:2],truth[:,:-1,:2]],1);active=((truth[:,:,2]>1e-6)|((truth[:,:,:2]-prev).abs().amax(-1)>1e-5))&valid;quiet=(~active)&valid
        na=active.sum(1);nq=quiet.sum(1);ng=(na>0).long()+(nq>0).long();length=valid.sum(1);w=torch.where(active,length[:,None]/(ng*na.clamp_min(1))[:,None],length[:,None]/(ng*nq.clamp_min(1))[:,None])*valid*self.replica[case,None]
        return pred,truth,initial,t,w,self.replica[case],self.gas_peak[case],valid

    @torch.no_grad()
    def predictions(self, model, ids, no_change=False):
        if bool(self.confirmation[ids].any()):assert self.confirmation_open,'Confirmation closed until both selections/winner freeze'
        full=[];display=[];mass_increases=[];projected_increases=[]
        for chunk in ids.split(16):
            b=len(chunk)
            if no_change:
                f=self.raw[chunk,0:1].expand(-1,90,-1);rolling=self.raw[chunk,:75,None].expand(-1,-1,16,-1)
            elif model is None:f=self.base[chunk];rolling=self.rb[chunk]
            else:
                f=model(self.x[chunk],self.base[chunk],self.raw[chunk,0],self.times[chunk]);origin=torch.arange(75,device=self.device);slots=origin[:,None]+torch.arange(17,device=self.device)[None];t=self.times[chunk][:,slots].reshape(b*75,17);initial=self.raw[chunk][:,origin].reshape(b*75,4);rolling=model(self.rx[chunk].reshape(b*75,16,46),self.rb[chunk].reshape(b*75,16,4),initial,t).reshape(b,75,16,4)
            full.append(f);display.append(torch.cat([f[:,:15],rolling[:,:,-1]],1));initial=self.raw[chunk,:75,:2];curve=torch.cat([initial[:,:,None],rolling[:,:,:,:2]],2);change=curve[:,:,1:]-curve[:,:,:-1];mass_increases.append(change.clamp_min(0).sum(2).mean(1));projected=torch.cat([initial.clamp_min(0)[:,:,None],rolling[:,:,:,:2]],2);projected_increases.append((projected[:,:,1:]-projected[:,:,:-1]).clamp_min(0).sum(2).mean(1))
        return torch.cat(full),torch.cat(display),dict(rolling_mean_mass_increase_from_raw_origin_kg=groups(torch.cat(mass_increases),self.config[ids]).tolist(),rolling_mean_mass_increase_from_projected_origin_kg=groups(torch.cat(projected_increases),self.config[ids]).tolist())

    @torch.no_grad()
    def score(self, model, ids, no_change=False):
        full,display,diagnostics=self.predictions(model,ids,no_change)
        args=(self.raw[ids],self.times[ids],self.config[ids],self.labels[ids],self.scales,self.std)
        return dict(autonomous=score_prediction(full,*args),display=score_prediction(display,*args,display=True),individual_forecasts=diagnostics)
