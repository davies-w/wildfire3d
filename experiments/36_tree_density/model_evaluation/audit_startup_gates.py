"""TRAIN-only frozen inference: distinguish learned gas-gate suppression from delta error."""
from pathlib import Path
import sys,json
import numpy as np,torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot01'
def main():
 sys.path.insert(0,str(D));from model import Transition
 torch.set_num_threads(4);a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());ids=np.array(meta['rotations'][0]['train']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);scale=torch.tensor(meta['physical_encoding_scales']);mean=ck['mean'];std=ck['std'];truth=torch.tensor(a['state'][ids]);times=torch.tensor(a['time'][ids]);geom=torch.tensor(a['geometry'][ids]);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;ext=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);z=(torch.asinh(truth/scale)-mean)/std;cfg=a['configuration'][ids];labels=a['activity_labels'][ids];results={};gates=None
 def grouped(v):return np.array([np.asarray(v)[cfg==c].mean(0) for c in np.unique(cfg)])
 for mode in ['original','gas_gate_forced_one']:
  model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
  if mode!='original':
   def force_one(module,args,out):
    v=out.clone();v[:,2]=50.;return v
   model.gate_head.register_forward_hook(force_one)
  hist=z[:,0:1].expand(-1,4,-1);memory=None;out=[];gg=[]
  with torch.inference_mode():
   for j in range(90):
    pred,memory=model.step(hist,ext[:,j],memory);gg.append(model.last_gate_logits[:,2].sigmoid().numpy());out.append((torch.sinh(pred*std+mean)*scale).numpy());hist=torch.cat([hist[:,1:],pred[:,None]],1)
  pred=np.stack(out,1);gate=np.stack(gg,1);tr=truth[:,1:].numpy();peak=np.abs(tr[:,:,2]).max(1);good=peak>0;mask=times[:,1:].numpy()<=32.2;deficit=(np.maximum(tr[:,:,2]-pred[:,:,2],0)*mask).max(1)/np.maximum(peak,1e-30);quiet=labels==0;den=quiet.sum(1);has=den>0
  r=dict(finite=bool(np.isfinite(pred).all()),startup_gas_p90_normalized_deficit=float(np.quantile(grouped(deficit),.9)),gas_peak_amplitude_MAE_kg_s=float(grouped(abs(pred[:,:,2].max(1)-tr[:,:,2].max(1))).mean()),full_rollout_state_MAE=grouped(abs(pred-tr).mean(1)).mean(0).tolist(),negative_state_fraction=grouped((pred<0).mean(1)).mean(0).tolist())
  if has.any():r['quiet_gas_MAE_kg_s']=float(np.mean([((abs(pred-tr)[:,:,2]*quiet).sum(1)/np.maximum(den,1))[has][cfg[has]==c].mean() for c in np.unique(cfg[has])]))
  if mode=='original':
   relevant=mask&(tr[:,:,2]>.1*peak[:,None]);v=gate[relevant];r['learned_gas_gate_during_startup_true_above10percent_peak']={'n_points':int(len(v)),'p10_median_p90':np.quantile(v,[.1,.5,.9]).tolist(),'fraction_below_half':float((v<.5).mean())};gates=gate
  results[mode]=r
 out=dict(train_only=True,histories=len(ids),configurations=len(np.unique(cfg)),optimizer_updates=0,scope='Frozen checkpoint183 autonomous CPU inference only. Learned gates are internal multipliers, not calibrated ignition probabilities or temperatures. Forced gas gate1 is a mechanistic counterfactual; the rollout changes its subsequent history too, so it is not an isolated direct-effect estimate or a validated replacement. No checkpoint modified, no test outcomes or training.',results=results)
 (R/'results/startup-gate-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
