"""Diagnose exact failing cache replay before accepting any wider tolerance."""
from pathlib import Path
import ast,hashlib,json,sys
import numpy as np
import torch
from joint_predictor import FrozenJointPredictor
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';C=R/'data/joint-decoder-candidate';F=R/'data/joint-rolling-features';sys.path.insert(0,str(S));from model import Transition
torch.set_num_threads(4);a=np.load(C/'features.npz');source=np.load(S/'data/sequences.npz');schema=json.loads((S/'schema.json').read_text());ids=a['source_ids'];raw=torch.tensor(source['state'][ids]);times=torch.tensor(source['time'][ids]);geometry=torch.tensor(source['geometry'][ids]);ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);model.eval();scales=torch.tensor(schema['physical_encoding_scales']);es=torch.tensor(schema['external_scales']);predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],scales,es);origin=1
with torch.inference_mode():
 _,features,states=predictor.forecast(raw[:,:origin+1],geometry,times[:,:origin+17],16,return_features=True)
 old=np.load(F/'features.npy',mmap_mode='r')[:,origin];old_states=np.load(F/'base-states.npy',mmap_mode='r')[:,origin];f=features.numpy();b=states.numpy();difference=np.abs(f-old);worst=np.argsort(difference.max((1,2)))[-8:];fail=~np.isclose(f,old,rtol=1e-5,atol=3e-6);state_difference=np.abs(b-old_states)
 z=(torch.asinh(raw[worst]/scales)-ck['mean'])/ck['std'];t=times[worst];g=geometry[worst];dt=t[:,1:]-t[:,:-1];on=(20-t[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([g[:,None].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/es
 names={'history_at','advance','prefix_memory'};nodes=[n for n in ast.parse((S/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];ns=dict(torch=torch,external=external);exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-original-prefix-reference','exec'),ns);ii=torch.arange(len(worst));jj=torch.full_like(ii,origin);hist=ns['history_at'](z,ii,jj);memory=ns['prefix_memory'](model,z,ii,jj);reference=[]
 for step in range(16):
  ex=external[:,origin+step];state,memory=model.step(hist,ex,memory);reference.append(torch.cat([state,memory,ex,t[:,origin+step+1,None]/180],-1));hist=ns['advance'](hist,state)
 reference=torch.stack(reference,1).numpy();_,small,_=predictor.forecast(raw[worst,:origin+1],geometry[worst],times[worst,:origin+17],16,return_features=True);small=small.numpy()
assert all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items())
out=dict(origin=origin,histories=len(ids),failing_feature_values=int(fail.sum()),affected_histories=int(fail.any((1,2)).sum()),max_feature_error_by_column=difference.max((0,1)).tolist(),max_state_absolute_error_by_state=state_difference.max((0,1)).tolist(),mean_state_absolute_error_by_state=state_difference.mean((0,1)).tolist(),worst_source_ids=ids[worst].tolist(),worst_subset_large_batch_vs_original_reference_max=float(np.abs(f[worst]-reference).max()),worst_subset_small_batch_vs_original_reference_max=float(np.abs(small-reference).max()),worst_subset_old_cache_vs_original_reference_max=float(np.abs(old[worst]-reference).max()),optimizer_updates=0,model_unchanged=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Feature replay diagnosis only; no fitted-head accuracy or holdout scoring. Original unidirectional prefix-memory/history functions are extracted from the frozen worker. Comparisons vary batch layout and prefix execution path, not inputs or weights.')
(R/'results/canonical-cache-replay-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
