"""Frozen-GRU features for every rolling16 origin used by the gallery.

Observed history is allowed only through each forecast's origin. No optimizer.
"""
from pathlib import Path
import ast,hashlib,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';C=R/'data/joint-decoder-candidate';D=R/'data/joint-rolling-features';sys.path.insert(0,str(S));from model import Transition
@torch.inference_mode()
def forecast_features(model,z,external,times,origins,mean,std,scales):
 b=len(z);count=len(origins);positions=(torch.arange(90)[:,None]+torch.arange(-3,1)[None]).clamp_min(0);histories=z[:,positions].reshape(b,90,16);inputs=torch.cat([histories,external],-1);observed,_=model.cell(inputs)
 history=z[:,(origins[:,None]+torch.arange(-3,1)[None]).clamp_min(0)].reshape(b*count,4,4);memory=observed[:,(origins-1).clamp_min(0)].clone();memory[:,origins==0]=0;memory=memory.reshape(b*count,32);features=[];states=[]
 for step in range(16):
  ex=external[:,origins+step].reshape(b*count,9);state,memory=model.step(history,ex,memory);features.append(torch.cat([state,memory,ex,times[:,origins+step+1].reshape(-1,1)/180],-1));states.append(torch.sinh(state*std+mean)*scales);history=torch.cat([history[:,1:],state[:,None]],1)
 return torch.stack(features,1).reshape(b,count,16,46),torch.stack(states,1).reshape(b,count,16,4)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def main():
 torch.set_num_threads(4);p=json.loads((C/'candidate-plan.json').read_text());source=np.load(R/'data/gas-head-candidate/features.npz');ids=source['source_ids'];assert len(ids)==sum(x['histories'] for x in p['partition_counts'].values());meta=json.loads((S/'schema.json').read_text());assert not set(ids)&set(meta['rotations'][0]['test']);a=np.load(S/'data/sequences.npz');raw=torch.tensor(a['state'][ids]);times=torch.tensor(a['time'][ids]);geom=torch.tensor(a['geometry'][ids]);scales=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scales)-mean)/std;model=Transition('gated');model.load_state_dict(ck['model']);model.eval();origins=torch.arange(75);D.mkdir(exist_ok=True)
 features=np.lib.format.open_memmap(D/'features.npy',mode='w+',dtype='float32',shape=(len(ids),75,16,46));base=np.lib.format.open_memmap(D/'base-states.npy',mode='w+',dtype='float32',shape=(len(ids),75,16,4))
 for start in range(0,len(ids),32):
  end=min(start+32,len(ids));f,b=forecast_features(model,z[start:end],external[start:end],times[start:end],origins,mean,std,scales);assert torch.isfinite(f).all() and torch.isfinite(b).all();features[start:end]=f.numpy();base[start:end]=b.numpy()
  if start%320==0:print(json.dumps(dict(prepared_histories=end,total=len(ids))),flush=True)
 features.flush();base.flush()
 # Independent replay of the original frozen prefix-memory/history functions.
 names={'history_at','advance','prefix_memory'};nodes=[n for n in ast.parse((S/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];ns=dict(torch=torch,external=external[:2]);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-prefix-reference','exec'),ns)
 with torch.inference_mode():
  for origin in [0,16,74]:
   ii=torch.tensor([0,1]);jj=torch.full_like(ii,origin);hist=ns['history_at'](z[:2],ii,jj);memory=ns['prefix_memory'](model,z[:2],ii,jj);ref=[]
   for step in range(16):
    ex=external[:2,origin+step];state,memory=model.step(hist,ex,memory);ref.append(torch.cat([state,memory,ex,times[:2,origin+step+1,None]/180],-1));hist=ns['advance'](hist,state)
   assert np.allclose(torch.stack(ref,1).numpy(),features[:2,origin],rtol=1e-5,atol=2e-6)
  changed=z[:1].clone();changed[:,17:]+=7.;original=forecast_features(model,z[:1],external[:1],times[:1],torch.tensor([16]),mean,std,scales)[0];counter=forecast_features(model,changed,external[:1],times[:1],torch.tensor([16]),mean,std,scales)[0];assert torch.equal(original,counter)
  assert np.allclose(base[:,0],source['base_states'][:,:16],rtol=1e-5,atol=2e-5)
 assert all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items());plan=dict(histories=len(ids),origins=list(range(75)),forecast_steps=16,feature_shape=list(features.shape),display_recipe='First15targets from full-origin0autonomous forecast, then last target of16step forecasts with observed-history origins0..74.',known_information='Observed state history through origin, frozen-GRU observed-prefix memory, geometry, ignition command, and actual saved time grid. No future target states enter forecast features.',source_case_order_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),scope='Frozen CPU inference only; complete TRAIN/head-selection/confirmation case order inherited from candidate-plan. No original test features, optimizer or fitted-decoder scores. Prefix reference and future-truth perturbation checks pass. Rolling forecast initial water estimate can be slightly negative, requiring an explicitly reported initial projection for nonnegative mass decoding.')
 (D/'rolling-plan.json').write_text(json.dumps(plan,indent=2)+'\n');proof=dict(prepared=True,optimizer_updates=0,files={q.name:dict(sha256=sha(q),bytes=q.stat().st_size) for q in D.iterdir() if q.is_file()},original_prefix_reference_close=True,future_truth_perturbation_invariant=True,origin0_first16_replay_close=True,base_GRU_unchanged=True,test_features_included=False);(R/'results/joint-rolling-features-prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'},indent=2))
if __name__=='__main__':main()
