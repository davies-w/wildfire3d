"""Fixed roles/cache plus objective metadata; no new future-state model inputs."""
import torch
from joint_data import JointData

class ContextData(JointData):
    def objective_metadata(self,ids,origins):
        assert bool(self.fit_allowed[ids].all())
        bases=[];labels=[];fulls=[]
        for full in [True,False]:
            use=origins<0 if full else origins>=0;n=ids[use]
            if not len(n):continue
            if full:base=self.base[n];label=self.labels[n]
            else:
                origin=origins[use];base=self.rb[n,origin];slots=origin[:,None]+torch.arange(16,device=self.device)[None];label=self.labels[n[:,None],slots];base=torch.cat([base,base[:,-1:].expand(-1,74,-1)],1);label=torch.cat([label,torch.full((len(n),74),-1,device=self.device,dtype=label.dtype)],1)
            bases.append(base);labels.append(label);fulls.append(torch.full((len(n),),full,device=self.device,dtype=torch.bool))
        return dict(base=torch.cat(bases),labels=torch.cat(labels),full=torch.cat(fulls))
