"""End-to-end frozen forecast using only an observed prefix and known forcing.

The corrected outputs never feed back into the base GRU. Times are the known
saved simulation grid; ignition is the dataset's imposed20second command.
This does not assert that future forcing is observable in real deployments.
"""
import torch

class FrozenJointPredictor:
    def __init__(self,base_model,mean,std,physical_scales,external_scales,decoder=None):
        self.base=base_model.eval();self.mean=mean;self.std=std;self.scales=physical_scales;self.external_scales=external_scales;self.decoder=decoder
        if decoder is not None:decoder.eval()

    @torch.inference_mode()
    def forecast(self,observed,geometry,times,steps,*,return_features=False):
        assert observed.ndim==3 and observed.shape[-1]==4 and 1<=observed.shape[1]<=91
        batch,length,_=observed.shape;origin=length-1;assert 1<=steps<=90-origin
        assert geometry.shape==(batch,7) and times.shape==(batch,length+steps)
        assert torch.isfinite(observed).all() and torch.isfinite(geometry).all() and torch.isfinite(times).all()
        dt=times[:,1:]-times[:,:-1];assert (dt>0).all()
        on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt
        external=torch.cat([geometry[:,None].expand(-1,len(dt[0]),-1),on[:,:,None],dt[:,:,None]],-1)/self.external_scales
        z=(torch.asinh(observed/self.scales)-self.mean)/self.std
        positions=(torch.arange(origin,device=z.device)[:,None]+torch.arange(-3,1,device=z.device)[None]).clamp_min(0)
        if origin:
            histories=z[:,positions].reshape(batch,origin,16);_,memory=self.base.cell(torch.cat([histories,external[:,:origin]],-1));memory=memory[-1]
        else:memory=torch.zeros(batch,32,device=z.device,dtype=z.dtype)
        last=(origin+torch.arange(-3,1,device=z.device)).clamp_min(0);history=z[:,last];features=[];states=[]
        for step in range(steps):
            ex=external[:,origin+step];state,memory=self.base.step(history,ex,memory)
            features.append(torch.cat([state,memory,ex,times[:,origin+step+1,None]/180],-1));states.append(torch.sinh(state*self.std+self.mean)*self.scales);history=torch.cat([history[:,1:],state[:,None]],1)
        features=torch.stack(features,1);raw=torch.stack(states,1)
        prediction=raw if self.decoder is None else self.decoder(features,raw,observed[:,-1],times[:,origin:])
        return (prediction,features,raw) if return_features else prediction
