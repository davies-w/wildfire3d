"""Terminal-only independent selection reconstruction and CPU forecast replay."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/joint-decoder-pilot02';O=R/'data/joint-decoder-pilot02-results'
sys.path.insert(0,str(D))
from joint_data import JointData
from joint_decoder import JointDecoder
from joint_metrics import select,choose_winner,checks
load=lambda p:json.loads(p.read_text())
proof=load(R/'results/joint-decoder-pilot02-collected.json');assert proof['passed'] and proof['experiment_complete'] and proof['cleanup_verified']
assert load(R/'results/joint-decoder-pilot02-permission-removed.json')['exact_grant_removed']
p=load(D/'trial-plan.json');freeze=load(O/'selection-freeze.json');comparison=load(O/'comparison.json');complete=load(O/'complete.json')
for name,digest in complete['manifest'].items():assert hashlib.sha256((O/name).read_bytes()).hexdigest()==digest,name
assert freeze['confirmation_scored'] is False and freeze['test_evaluated'] is False
assert complete['selection_frozen_before_confirmation'] and not comparison['test_evaluated']
torch.set_num_threads(4);d=JointData(D);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);baseline=load(O/'selection-baseline.json');selections=[];reports=[]
# Reconstruct decisions exclusively from selection artifacts before opening confirmation.
for arm in p['arms']:
 rows=[dict(epoch=-1,metrics=baseline),dict(epoch=0,metrics=load(O/(arm+'-untrained-selection.json')))]+[load(O/f'{arm}-epoch{ep:03}.json') for ep in range(10,301,10)]
 best,accepted=select(baseline,rows,p['acceptance'],d.scales.tolist());s=load(O/(arm+'-selection.json'));assert s['row']==best and s['epoch']==best['epoch'] and s['accepted_on_selection']==accepted
 assert s==next(x for x in freeze['arms'] if x['arm']==arm);selections.append(s)
assert choose_winner(baseline,selections)==freeze['winner']==comparison['winner']
d.confirmation_open=True
for s in selections:
 arm=s['arm'];ck=torch.load(O/(arm+'-selected.pt'),map_location='cpu',weights_only=False);assert ck['epoch']==s['epoch'] and ck['apply_decoder']==s['apply_decoder']==(s['epoch']>=0)
 digest=hashlib.sha256(b''.join(v.numpy().tobytes() for v in ck['model'].values())).hexdigest();assert digest==s['model_sha256']
 m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,arm);m.load_state_dict(ck['model']);m.eval()
 with torch.inference_mode():cpu=d.score(m if s['apply_decoder'] else None,d.roles['confirmation'])
 gpu=load(O/(arm+'-confirmation.json'));close={}
 for regime in ['autonomous','display']:
  a,b=cpu[regime],gpu[regime];close[regime]=bool(np.allclose(a['physical_MAE_by_feature'],b['physical_MAE_by_feature'],rtol=.002,atol=1e-7) and np.isclose(a['objective'],b['objective'],rtol=.002,atol=1e-8) and abs(a['startup_gas_p90_deficit']-b['startup_gas_p90_deficit'])<=.002)
 ckchecks=checks(load(O/'confirmation-baseline.json'),gpu,p['acceptance'],d.scales.tolist());assert ckchecks==comparison['arms'][arm]['checks']
 reports.append(dict(arm=arm,epoch=s['epoch'],apply_decoder=s['apply_decoder'],selected_hash_exact=True,selection_reconstructed=True,cpu_replay_close=close,cpu_metrics=cpu,gpu_metrics=gpu))
w=freeze['winner'];winning=checks(load(O/'confirmation-baseline.json'),load(O/'confirmation-baseline.json'),p['acceptance'],d.scales.tolist()) if w=='raw_baseline' else comparison['arms'][w]['checks'];assert winning==comparison['checks'] and comparison['passed']==(w!='raw_baseline' and all(winning.values()))
out=dict(passed=all(all(r['cpu_replay_close'].values()) for r in reports),repair_acceptance_passed=comparison['passed'],winner=w,checks=winning,arms=reports,selection_and_winner_independently_reconstructed=True,optimizer_updates=0,test_evaluated=False,scope=p['partition_limitation'],cpu_cuda_tolerance='0.2% relative for state MAE/objective; startup p90 absolute0.002. Discrete near-tied peak timing can differ.')
(R/'results/joint-decoder-pilot02-analysis.json').write_text(json.dumps(out,indent=2)+'\n');assert out['passed'];print(json.dumps({k:v for k,v in out.items() if k!='arms'},indent=2))
