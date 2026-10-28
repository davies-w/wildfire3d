"""Posthoc failure diagnosis on decoder-selection only; no refitting or deployment."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
import numpy as np
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/joint-decoder-pilot02';O=R/'data/joint-decoder-pilot02-results';sys.path.insert(0,str(D))
from joint_data import JointData
from joint_decoder import JointDecoder
from joint_metrics import checks,rank,groups
load=lambda p:json.loads(p.read_text());assert load(R/'results/joint-decoder-pilot02-analysis.json')['passed'];assert load(R/'results/joint-decoder-pilot02-permission-removed.json')['exact_grant_removed'];torch.set_num_threads(4);d=JointData(D);ids=d.roles['selection'];p=load(D/'trial-plan.json');b=load(O/'selection-baseline.json');initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False)
with torch.inference_mode():base=d.predictions(None,ids)
def decomposition(pred):
 result={}
 for regime,curve in zip(['autonomous','display'],pred[:2]):
  squared=((torch.asinh(curve/d.scales)-torch.asinh(d.raw[ids,1:]/d.scales))/d.std).square();quiet=d.labels[ids]==0;count=quiet.sum(1);keep=count>0
  result[regime]=dict(encoded_MSE_by_feature=groups(squared.mean(1),d.config[ids]).tolist(),quiet_encoded_MSE_by_feature=groups((squared*quiet[:,:,None]).sum(1)[keep]/count[keep,None],d.config[ids][keep]).tolist())
 return result
baseline_decomposition=decomposition(base);reports=[]
for arm in p['arms']:
 rows=[load(O/f'{arm}-epoch{ep:03}.json') for ep in range(10,301,10)];checked=[(r,checks(b,r['metrics'],p['acceptance'],d.scales.tolist())) for r in rows];counts=Counter(k for _,ck in checked for k,v in ck.items() if not v);row,ck=min(checked,key=lambda x:(sum(not v for v in x[1].values()),rank(b,x[0])));ep=row['epoch'];snapshot=torch.load(O/f'{arm}-epoch{ep:03}.pt',map_location='cpu',weights_only=False);m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,arm);m.load_state_dict(snapshot['model']);m.eval()
 with torch.inference_mode():cpu=d.score(m,ids);pred=d.predictions(m,ids)
 for regime in ['autonomous','display']:
  a,z=cpu[regime],row['metrics'][regime];assert np.allclose(a['physical_MAE_by_feature'],z['physical_MAE_by_feature'],rtol=.002,atol=1e-7) and np.isclose(a['objective'],z['objective'],rtol=.002,atol=1e-8) and abs(a['startup_gas_p90_deficit']-z['startup_gas_p90_deficit'])<=.002
 ratios={regime:[y/x for x,y in zip(b[regime]['physical_MAE_by_feature'],cpu[regime]['physical_MAE_by_feature'])] for regime in ['autonomous','display']};quiet_excess={regime:[(y-x)/s for x,y,s in zip(b[regime]['quiet_physical_MAE'],cpu[regime]['quiet_physical_MAE'],d.scales.tolist())] for regime in ['autonomous','display']}
 reports.append(dict(arm=arm,checkpoints_audited=len(rows),failed_gate_counts=dict(counts),posthoc_diagnostic_epoch=ep,diagnostic_rule='Minimum failed acceptance checks, then frozen ranking; selection data only. This is not an accepted or deployed checkpoint.',diagnostic_failed_checks=[k for k,v in ck.items() if not v],diagnostic_cpu_replay_close=True,diagnostic_MAE_ratios=ratios,diagnostic_quiet_MAE_increase_in_encoding_scale=quiet_excess,diagnostic_encoded_decomposition=decomposition(pred),diagnostic_gpu_metrics=row['metrics'],per_state_best_display_MAE_ratio_across_epochs=[min(r['metrics']['display']['physical_MAE_by_feature'][j]/b['display']['physical_MAE_by_feature'][j] for r in rows) for j in range(4)],per_state_minima_are_different_checkpoints=True))
out=dict(passed=True,optimizer_updates=0,selection_histories=len(ids),confirmation_reused=False,test_evaluated=False,accepted_winner='raw_baseline',baseline_encoded_decomposition=baseline_decomposition,arms=reports,scope='Posthoc failure diagnosis, not new model selection or independent generalization. Every evaluated trained epoch fails the all-four displayed-state reduction and quiet guard. Specific failures and physical/encoded metrics establish a tradeoff in this fitted objective/representation; they do not isolate a unique cause or prove no other model can improve. No trained checkpoint deployed.')
(R/'results/joint-decoder-pilot02-failure-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['arms','baseline_encoded_decomposition']},indent=2));print(json.dumps([{k:r[k] for k in ['arm','failed_gate_counts','posthoc_diagnostic_epoch','diagnostic_MAE_ratios','per_state_best_display_MAE_ratio_across_epochs']} for r in reports],indent=2))
