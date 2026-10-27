"""CPU inference/structure checks only; do not execute an optimizer or worker entrypoint."""
import ast,json,sys,hashlib,tarfile
from pathlib import Path
import numpy as np,torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot01'
def main():
 p=json.loads((R/'results/exposure-pilot-prepared.json').read_text());assert hashlib.sha256((D/'inputs.tar').read_bytes()).hexdigest()==p['input_sha256']
 for n,h in p['files'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
 with tarfile.open(D/'inputs.tar') as t:
  assert len(t.getmembers())==len(p['files'])+1
  for n,h in p['files'].items():assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==h
 tree=ast.parse((D/'worker.py').read_text());functions=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))];ns={'torch':torch,'np':np};exec(compile(ast.Module(body=functions,type_ignores=[]),'worker-functions','exec'),ns)
 sys.path.insert(0,str(D));from model import Transition,normalize_fit
 torch.set_num_threads(4);a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);ck=torch.load(D/'data/initial.pt',map_location='cpu',weights_only=False);mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
 ns.update(device='cpu',config=config,external=external,raw=raw,times=times,scale=scale,dt=dt,active=active,activity_labels=torch.tensor(a['activity_labels']),z=z,mean=mean,std=std)
 train=torch.tensor(meta['rotations'][0]['train']);valid=torch.tensor(meta['rotations'][0]['validation']);assert not set(train.tolist())&set(valid.tolist());fm,fs=normalize_fit(raw,train,config,scale);assert torch.allclose(fm,mean,rtol=1e-6,atol=1e-6) and torch.allclose(fs,std,rtol=1e-6,atol=1e-6)
 model=Transition('gated');model.load_state_dict(ck['model']);model.eval()
 with torch.inference_mode():
  report=ns['evaluate'](model,z,valid[:8],mean,std);diag=ns['diagnostics'](model,valid[:8]);assert diag['finite'] and report['rollout']['finite'];json.dumps(dict(report=report,diagnostics=diag),allow_nan=False)
  # Independent startup p90 and physical MAE reference on validation prefix only.
  pred=ns['predictions'](model,z,valid[:8],True);phys=torch.sinh(pred*std+mean)*scale;truth=raw[valid[:8],1:];peak=truth[:,:,2].abs().amax(1);mask=times[valid[:8],1:]<=32.2;deficit=((truth[:,:,2]-phys[:,:,2]).clamp_min(0)*mask).amax(1)/peak.clamp_min(1e-30);ids=valid[:8][peak>0];dd=deficit[peak>0];gg=torch.stack([dd[config[ids]==c].mean() for c in torch.unique(config[ids])]);assert abs(diag['startup_gas_p90_deficit']-float(torch.quantile(gg,.9)))<1e-7
  # Cached observed-prefix memory agrees with the original teacher-forced GRU convention.
  ids=train[:4];js=torch.tensor([0,1,8,31]);memory=ns['prefix_memory'](model,z,ids,js)
  for n,j,mem in zip(ids.tolist(),js.tolist(),memory):
   expected=torch.zeros(32)
   if j:
    ii=torch.full((j,),n);jj=torch.arange(j);hist=ns['history_at'](z,ii,jj);outputs,_=model.cell(model.inputs(hist,external[ii,jj])[None]);expected=outputs[0,-1]
   assert torch.allclose(mem,expected,rtol=1e-5,atol=1e-7)
 worker=(D/'worker.py').read_text();assert "load_state_dict(copy.deepcopy(initial['optimizer']))" in worker;assert "for treatment in [False,True]:" in worker;assert 'range(59)' in worker;assert "183+ep" in worker;assert "test_evaluated=False" in worker
 proof=dict(passed=True,worker_sha256=p['files']['worker.py'],package_member_hashes=True,actual_saved_normalization_matches_train=True,validation_report_path_finite=True,startup_diagnostic_independent_replay=True,prefix_memory_reference_match=True,optimizer_states_deepcopied=True,optimizer_updates=0,local_training=False,test_metrics_read=False,cloud_replay_still_required=True)
 (R/'results/exposure-pilot-offline-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
