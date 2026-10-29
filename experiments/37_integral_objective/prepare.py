from pathlib import Path
import json,shutil,hashlib
import numpy as np
R=Path(__file__).resolve().parent;OLD=R.parent/'36_tree_density';SRC=OLD/'data/pair-sequence/rotation0';D=R/'data/training01';(D/'data').mkdir(parents=True,exist_ok=True)
for n in ['model.py','gated_model.py','plain_model.py','schema.json','data/sequences.npz','runtime.py']:
 shutil.copy2(SRC/n,D/n)
shutil.copy2(R/'objective.py',D/'objective.py')
p=json.loads((SRC/'coverage-plan.json').read_text());p.update(experiment='37 integral-objective gated GRU rotation0',arms=['gated'],architecture='Unchanged gated GRU 25->32, four outputs, three soft output gates,5895 parameters',selection='Mean four-feature autonomous full-sequence range-normalized absolute integral on validation; freeze before test',training_balance='Equal configurations through inverse replica counts; remove old active/quiet transition reweighting to align with whole-sequence objective',thermal_loss='Mean of all four physical-space normalized absolute integrals',gate_loss_weight=.1,scorecard='All four full-sequence integral percentages, old diagnostics retained');p['budget']={'soft_seconds':45000,'maximum_allowance_usd':16.0};(D/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
(D/'runtime.py').write_text((D/'runtime.py').read_text().replace('density36/pair-sequence01/rotation0/','integral37/training01/'))
s=(SRC/'worker.py').read_text();s=s.replace('from runtime import upload','from runtime import upload\nfrom objective import interval_error,sequence_score')
s=s.replace("device='cuda';", "device='cuda';")
s=s.replace("dt=times[:,1:]", "ranges=raw_full.amax(1)-raw_full.amin(1)\nassert bool((ranges>0).all()),'Undefined zero-range feature'\ndt=times[:,1:]")
# Selection uses all4 physical-space integral scores, retains old normalized MSE as diagnostic.
s=s.replace("finite=bool(torch.isfinite(phys).all() and torch.isfinite(err).all());entry=", "legacy=err\n  curves=torch.cat([raw[ids,:1],phys],1);integrals=sequence_score(curves,raw[ids],times[ids],ranges[ids]);err=integrals.mean(-1)\n  finite=bool(torch.isfinite(phys).all() and torch.isfinite(err).all());entry=")
s=s.replace("errors=(phys-raw[ids,1:]).abs();", "entry['integral_error_percent_by_feature']=(100*mean_groups(integrals,ids)).cpu().tolist();entry['legacy_three_state_normalized_mse']=float(mean_groups(legacy,ids))\n  errors=(phys-raw[ids,1:]).abs();")
begin=s.index(' # Equal active/quiet contribution');end=s.index(' best=1e30',begin)
s=s[:begin]+" # All windows have equal configuration weight; no old active/quiet weights.\n replica_weights=torch.zeros(2080,device=device)\n for n in train.tolist():replica_weights[n]=1/int((config[train]==config[n]).sum())\n"+s[end:]
begin=s.index('   for step in range(h):');end=s.index("assert bool(torch.isfinite(loss))",begin)
s=s[:begin]+'''   left_error=torch.zeros(len(ids),4,device=device);state_integral=torch.zeros(len(ids),4,device=device);gate_integral=torch.zeros(len(ids),device=device)
   duration=times[ids,js+h]-times[ids,js]
   for step in range(h):
    jj=js+step;state,memory=model.step(hist,external[ids,jj],memory)
    physical=torch.sinh(state*std+mean)*scale;right_error=physical-raw[ids,jj+1]
    state_integral=state_integral+interval_error(left_error,right_error)*dt[ids,jj,None]
    supervised=gate_supervised[ids,jj];bce=F.binary_cross_entropy_with_logits(model.last_gate_logits,gate_targets[ids,jj],reduction='none')
    gate_integral=gate_integral+dt[ids,jj]*(bce*supervised).sum(-1)/supervised.sum(-1).clamp_min(1)
    left_error=right_error;hist=advance(hist,state)
   state_per_window=(state_integral/(duration[:,None]*ranges[ids])).mean(-1)
   gate_per_window=gate_integral/duration
   loss=((state_per_window+P['gate_loss_weight']*gate_per_window)*replica_weights[ids]).sum()/replica_weights[ids].sum();''' +s[end:]
s=s.replace('assert len(reports)==2','assert len(reports)==1').replace('folds=2','folds=1').replace('all tests gated behind ten selections','single gated selection frozen before test').replace("scope='Plain and soft-gated four-state GRUs on one fixed grouped8/1/1 split, stride-one full windows at every curriculum stage; both selections before tests. Previously examined data; not ten-fold aggregate. Overlap changes optimizer updates and transition exposure.'", "scope='Integral-loss gated GRU on unchanged rotation0 train8/val1/test1 split. Four-state range-normalized integral selection; no test-driven tuning. Previously examined data.'")
compile(s,'worker.py','exec');(D/'worker.py').write_text(s)
a=np.load(D/'data/sequences.npz');meta=json.loads((D/'schema.json').read_text());rot=meta['rotations'][0];train=rot['train'];ranges=np.ptp(a['state'][train],axis=1)
proof=dict(passed=bool((ranges>0).all()),training_histories=len(train),validation_histories=len(rot['validation']),test_histories=len(rot['test']),train_range_min=ranges.min(0).tolist(),train_range_median=np.median(ranges,axis=0).tolist(),split_sha256=hashlib.sha256((D/'schema.json').read_bytes()).hexdigest(),gated_model_unchanged=(D/'gated_model.py').read_bytes()==(SRC/'gated_model.py').read_bytes(),test_used_for_recipe=False,local_training=False)
(R/'results/prepared.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
