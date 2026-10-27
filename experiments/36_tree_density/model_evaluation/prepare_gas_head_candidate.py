"""Prepare TRAIN/validation frozen features; no fitting, optimizer or cloud launch."""
from pathlib import Path
import hashlib,json,sys,shutil
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02';OUT=R/'data/gas-head-candidate'
sys.path.insert(0,str(D));from model import Transition
from gas_head import GasHead
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 torch.set_num_threads(4);torch.manual_seed(3617)
 meta=json.loads((D/'schema.json').read_text());rot=meta['rotations'][0];ids=rot['train']+rot['validation'];assert len(ids)==len(set(ids)) and not set(ids)&set(rot['test'])
 a=np.load(D/'data/sequences.npz');raw=torch.tensor(a['state'][ids]);times=torch.tensor(a['time'][ids]);geom=torch.tensor(a['geometry'][ids]);config=torch.tensor(a['configuration'][ids]);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);model.eval();mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;history=z[:,0:1].expand(-1,4,-1);memory=None;features=[];states=[]
 with torch.inference_mode():
  for j in range(90):
   state,memory=model.step(history,external[:,j],memory);features.append(torch.cat([state,memory,external[:,j],times[:,j+1,None]/180],-1));states.append(torch.sinh(state*std+mean)*scale);history=torch.cat([history[:,1:],state[:,None]],1)
 features=torch.stack(features,1).clone();states=torch.stack(states,1).clone();assert features.shape==(len(ids),90,46) and torch.isfinite(features).all() and torch.isfinite(states).all()
 ntrain=len(rot['train']);train_features=features[:ntrain];means=[];seconds=[]
 for c in torch.unique(config[:ntrain]):
  x=train_features[config[:ntrain]==c];means.append(x.mean((0,1)));seconds.append(x.square().mean((0,1)))
 fm=torch.stack(means).mean(0);fs=(torch.stack(seconds).mean(0)-fm.square()).clamp_min(0).sqrt().clamp_min(.05);head=GasHead(fm,fs);head.eval()
 with torch.inference_mode():baseline=head(features,states[:,:,2])
 assert torch.equal(baseline,states[:,:,2]);assert all(torch.equal(value,ck['model'][name]) for name,value in model.state_dict().items())
 OUT.mkdir(exist_ok=True);np.savez_compressed(OUT/'features.npz',features=features.numpy(),base_states=states.numpy(),truth=raw.numpy(),time=times.numpy(),configuration=config.numpy(),source_ids=np.array(ids),activity_labels=a['activity_labels'][ids]);torch.save(dict(model=head.state_dict(),feature_mean=fm,feature_std=fs),OUT/'initial-head.pt');shutil.copyfile(R/'model_evaluation/gas_head.py',OUT/'gas_head.py')
 (OUT/'base-normalization.json').write_text(json.dumps(dict(mean=mean.tolist(),std=std.tolist(),physical_encoding_scales=scale.tolist()),indent=2)+'\n')
 plan=dict(status='prepared_not_launched',candidate='bounded_output_only_gas_head',base_checkpoint_sha256=sha(D/'data/initial.pt'),base_epoch=ck['epoch'],train_histories=ntrain,validation_histories=len(rot['validation']),test_histories=0,train_indices=list(range(ntrain)),validation_indices=list(range(ntrain,len(ids))),features=['base_encoded_prediction_4','base_GRU_hidden_32','existing_external_9','target_elapsed_seconds_div180'],parameter_count=sum(p.numel() for p in head.parameters()),factor_bounds=[.5,2],initial_output_bitwise_equal_to_base=True,base_parameters_unchanged=True,feedback='None: corrected gas is an output calibration only. GRU memory and all four base trajectories remain unchanged; corrected gas is not used by later recurrent steps.',normalization='Train-only equal-configuration feature moments across actual saved endpoints; std floor0.05.',scope='Partial gas repair candidate, not a repair of water/dry-fuel/heating or learned recurrent dynamics. Known actual dt and ignition command match existing model inputs. Elapsed time is added; timing audit does not establish it as the cause. No optimizer instantiated, fitting, validation scoring, test features or cloud launch. Any future trained correction must retain original acceptance plus safeguards for gas integral, peak timing and dry-fuel/gas consistency; passing this partial candidate alone cannot complete the broader goal.',physical_scope='Generic3m diameter conical crowns, crown heights4/6/8/10m above2m base,1600weighted particles,0.5m mesh in24x16x16m, imposed1500C contact ignition20s, horizon180s. No trunks/buildings/embers/convergence study or physical validation. Gas is vegetation fuel release, not combustion HRR; dry fuel is derived from release/0.75 and heating is a surface-heating index.')
 (OUT/'candidate-plan.json').write_text(json.dumps(plan,indent=2)+'\n');proof=dict(prepared=True,submitted=False,optimizer_updates=0,validation_scored=False,files={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in OUT.iterdir() if p.is_file()},initial_output_bitwise_equal=True,base_parameters_unchanged=True,train_validation_identity_isolation=True,test_features_included=False)
 (R/'results/gas-head-candidate-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in plan.items() if k not in ['train_indices','validation_indices']},indent=2))
if __name__=='__main__':main()
