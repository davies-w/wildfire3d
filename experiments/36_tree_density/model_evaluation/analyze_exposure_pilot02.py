"""Verify frozen selections and replay validation inference after terminal collection only."""
from pathlib import Path
import ast,json,sys,hashlib
import numpy as np,torch
R=Path(__file__).resolve().parents[1];D=R/'data/exposure-pilot02';OUT=R/'data/exposure-pilot02-results'
def main():
 proof=json.loads((R/'results/exposure-pilot02-collected.json').read_text());assert proof['passed'] and proof['experiment_complete'] and proof['cleanup_verified'],'Wait for complete verified collection'
 plan=json.loads((D/'pilot-plan.json').read_text());freeze=json.loads((OUT/'selection-freeze.json').read_text());comparison=json.loads((OUT/'comparison.json').read_text());assert freeze['test_evaluated'] is False and comparison['test_evaluated'] is False
 sys.path.insert(0,str(D));from model import Transition
 torch.set_num_threads(4);a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());valid=torch.tensor(meta['rotations'][0]['validation']);assert not set(valid.tolist())&set(meta['rotations'][0]['test'])
 raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);config=torch.tensor(a['configuration']);scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5)
 names={'objective','history_at','advance','phase_mae','prefix_memory','predictions','evaluate','mean_groups','diagnostics'};nodes=[n for n in ast.parse((D/'worker.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
 ns=dict(torch=torch,np=np,device='cpu',config=config,external=external,raw=raw,times=times,scale=scale,dt=dt,active=active,activity_labels=torch.tensor(a['activity_labels']));exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-inference-only','exec'),ns)
 reports=[]
 for arm in ['original','corrected']:
  rows=[json.loads((OUT/f'{arm}-baseline.json').read_text())]+[json.loads((OUT/f'{arm}-epoch{i:03}.json').read_text()) for i in range(1,13)];expected=min(rows,key=lambda r:r['validation']['rollout']['objective']);selection=json.loads((OUT/f'{arm}-selection.json').read_text());assert selection['epoch']==expected['epoch'] and selection['row']==expected
  ck=torch.load(OUT/f'{arm}-selected.pt',map_location='cpu',weights_only=False);model=Transition('gated');model.load_state_dict(ck['model']);model.eval();sha=hashlib.sha256(b''.join(v.numpy().tobytes() for v in model.state_dict().values())).hexdigest();assert sha==selection['model_sha256'] and ck['epoch']==selection['epoch']
  mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std;ns.update(z=z,mean=mean,std=std)
  with torch.inference_mode():replay=ns['evaluate'](model,z,valid,mean,std);diag=ns['diagnostics'](model,valid)
  saved=expected['validation']['rollout'];cpu=replay['rollout'];assert cpu['finite'] and diag['finite']
  normalized_mae_difference=(abs(np.array(cpu['physical_MAE_by_feature'])-saved['physical_MAE_by_feature'])/scale.numpy()).tolist();startup_difference=abs(diag['startup_gas_p90_deficit']-expected['diagnostics']['startup_gas_p90_deficit']);close=bool(np.allclose(cpu['physical_MAE_by_feature'],saved['physical_MAE_by_feature'],rtol=.002,atol=0) and startup_difference<=.002)
  reports.append(dict(arm=arm,selected_epoch=selection['epoch'],selected_state_hash_exact=True,selection_original_objective_argmin_verified=True,gpu_row=expected,cpu_validation_replay=replay,cpu_diagnostics=diag,cpu_vs_gpu_normalized_MAE_difference=normalized_mae_difference,cpu_vs_gpu_startup_p90_difference=startup_difference,cpu_replay_close=close))
 b,c=[x['gpu_row'] for x in reports];br=b['validation']['rollout'];cr=c['validation']['rollout'];bd=b['diagnostics'];cd=c['diagnostics'];k=plan['acceptance_all_required'];ss=scale.tolist()
 def improve(old,new,f):return old is not None and new is not None and old>0 and new<=old*(1-f)
 def bounded(old,new,f):return old is not None and new is not None and new<=old*(1+f)
 checks=dict(startup_gas=improve(bd['startup_gas_p90_deficit'],cd['startup_gas_p90_deficit'],k['startup_0_to32s_gas_p90_normalized_deficit_relative_reduction_at_least']),peak_amplitude=improve(br['peak_release_MAE_kg_s'],cr['peak_release_MAE_kg_s'],k['gas_peak_amplitude_MAE_relative_reduction_at_least']),original_objective=bounded(br['objective'],cr['objective'],k['original_validation_objective_relative_increase_at_most']),each_state_MAE=all(bounded(x,y,k['full_rollout_each_state_MAE_relative_increase_at_most']) for x,y in zip(br['physical_MAE_by_feature'],cr['physical_MAE_by_feature'])),quiet_MAE=bd['quiet_physical_MAE'] is not None and cd['quiet_physical_MAE'] is not None and all((y-x)/s<=k['quiet_state_MAE_absolute_increase_at_most_in_physical_encoding_scale_units'] for x,y,s in zip(bd['quiet_physical_MAE'],cd['quiet_physical_MAE'],ss)),finite=bd['finite'] and cd['finite'])
 assert checks==comparison['checks'] and all(checks.values())==comparison['passed']
 out=dict(passed=all(x['cpu_replay_close'] for x in reports),comparison_acceptance_passed=comparison['passed'],checks=checks,independent_acceptance_recomputed=True,all_selections_original_objective_argmin=True,test_evaluated=False,optimizer_updates=0,scope='Post-collection verification of frozen validation results only; CPU and CUDA inference may differ in reduction order and library version. Previously inspected validation is development evidence, not pristine confirmation. No selection or acceptance changes.',arms=reports)
 (R/'results/exposure-pilot02-analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps({key:value for key,value in out.items() if key!='arms'},indent=2))
if __name__=='__main__':main()
