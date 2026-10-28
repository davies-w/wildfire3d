"""Fit-only quiet-count/replica metadata for loss aggregation; forecast inputs unchanged."""
import numpy as np
import torch
from context_data import ContextData

class GuardMatchedData(ContextData):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        fit=self.roles['fit'];indices=fit.cpu().numpy();labels=self.labels[fit].cpu().numpy();configuration=self.config[fit].cpu().numpy();counts=(labels==0).sum(1);keep=counts>0
        q=np.zeros(len(self.raw),dtype=np.float32);w=np.zeros_like(q);q[indices]=counts
        unique,inverse,replicas=np.unique(configuration[keep],return_inverse=True,return_counts=True)
        w[indices[keep]]=1/replicas[inverse]
        self.quiet_count=torch.tensor(q,device=self.device);self.quiet_replica_weight=torch.tensor(w,device=self.device);self.quiet_normalization=len(fit)/len(unique) if len(unique) else 0.
        self.quiet_fit_configurations=len(unique)

    def objective_metadata(self,ids,origins):
        metadata=super().objective_metadata(ids,origins)
        # training_batch groups full rows before rolling rows; preserve that order.
        ordered=torch.cat([ids[origins<0],ids[origins>=0]])
        metadata.update(quiet_count=self.quiet_count[ordered],quiet_replica_weight=self.quiet_replica_weight[ordered],quiet_normalization=self.quiet_normalization)
        return metadata
