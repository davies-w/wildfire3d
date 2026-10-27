# Appended to the frozen worker function definitions; never execute this file alone.
import copy
PLAN=json.loads((R/'pilot-plan.json').read_text())
assert PLAN['continuation_epochs_per_arm']==12 and PLAN['horizon_steps']==32
initial=torch.load(R/'data/initial.pt',map_location=device,weights_only=False)
assert initial['epoch']==183 and initial['kind']=='gated' and len(initial['optimizer']['state'])>0
rotation=meta['rotations'][0]
train=torch.tensor(rotation['train'],device=device);valid=torch.tensor(rotation['validation'],device=device)
assert not set(train.tolist())&set(valid.tolist())
assert not (set(train.tolist())|set(valid.tolist()))&set(rotation['test'])
mean=initial['mean'].to(device);std=initial['std'].to(device);z=(torch.asinh(raw/scale)-mean)/std
fit_mean,fit_std=normalize_fit(raw,train,config,scale)
assert torch.allclose(mean,fit_mean,rtol=1e-6,atol=1e-6) and torch.allclose(std,fit_std,rtol=1e-6,atol=1e-6)
weights=torch.zeros(len(raw),90,device=device)
for n in train.tolist():
 ac=active[n];na=int(ac.sum());nq=90-na;groups=int(na>0)+int(nq>0);replicas=int((config[train]==config[n]).sum())
 weights[n]=torch.where(ac,90/(groups*max(na,1)),90/(groups*max(nq,1)))/replicas
factors=exposure_target_factors(weights,train,32)

def fresh():
 m=Transition('gated').to(device);m.load_state_dict(initial['model']);opt=torch.optim.AdamW(m.parameters(),lr=3e-4,weight_decay=1e-4);opt.load_state_dict(copy.deepcopy(initial['optimizer']));restore_rng(initial['rng']);return m,opt

@torch.no_grad()
def diagnostics(model,ids):
 model.eval();pred=predictions(model,z,ids,True);phys=torch.sinh(pred*std+mean)*scale;truth=raw[ids,1:];finite=bool(torch.isfinite(phys).all())
 if not finite:return {'finite':False}
 startup=times[ids,1:]<=32.2;peak=truth[:,:,2].abs().amax(1);good=peak>0;deficit=((truth[:,:,2]-phys[:,:,2]).clamp_min(0)*startup).amax(1)/peak.clamp_min(1e-30)
 unique=torch.unique(config[ids][good]);grouped=torch.stack([deficit[good][config[ids][good]==c].mean() for c in unique]) if len(unique) else None
 quiet=activity_labels[ids]==0;den=quiet.sum(1);keep=den>0
 quietmae=mean_groups(((phys-truth).abs()*quiet[:,:,None]).sum(1)[keep]/den[keep,None],ids[keep]) if bool(keep.any()) else None
 return dict(finite=True,startup_gas_p90_deficit=float(torch.quantile(grouped,.9)) if grouped is not None else None,startup_gas_median_deficit=float(grouped.median()) if grouped is not None else None,zero_gas_peak_histories=int((~good).sum()),startup_gas_eligible_configurations=len(unique),quiet_physical_MAE=quietmae.cpu().tolist() if quietmae is not None else None,quiet_eligible_histories=int(keep.sum()))

def train_batch(model,opt,ids,js,treatment):
 model.train();hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js);loss=0.
 for step in range(32):
  jj=js+step;state,memory=model.step(hist,external[ids,jj],memory);state_loss=training_objective(state,z[ids,jj+1]);supervised=gate_supervised[ids,jj];bce=F.binary_cross_entropy_with_logits(model.last_gate_logits,gate_targets[ids,jj],reduction='none');state_loss+=P['gate_loss_weight']*(bce*supervised).sum(-1)/supervised.sum(-1).clamp_min(1)
  multiplier=factors[jj] if treatment else 1.;loss+=(state_loss*weights[ids,jj]*multiplier).sum();hist=advance(hist,state)
 loss=loss/(len(ids)*32);assert bool(torch.isfinite(loss));opt.zero_grad(set_to_none=True);loss.backward();assert all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters());torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();return float(loss)

# Replay a real training batch from the nonempty saved optimizer, isolated from both arms.
replay=[]
for treatment in [False,True]:
 ids=train[:8];js=torch.zeros_like(ids)
 m,o=fresh();loss1=train_batch(m,o,ids,js,treatment);snapshot=copy.deepcopy(dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate()))
 expected=train_batch(m,o,ids,js,treatment);expected_state=copy.deepcopy(m.state_dict());expected_opt=copy.deepcopy(o.state_dict())
 mm,oo=fresh();mm.load_state_dict(snapshot['model']);oo.load_state_dict(snapshot['optimizer']);restore_rng(snapshot['rng']);actual=train_batch(mm,oo,ids,js,treatment)
 assert expected==actual and all(torch.equal(v,mm.state_dict()[k]) for k,v in expected_state.items())
 for key,value in expected_opt['state'].items():
  for name,entry in value.items():assert torch.equal(entry,oo.state_dict()['state'][key][name]) if torch.is_tensor(entry) else entry==oo.state_dict()['state'][key][name]
 replay.append(dict(corrected=treatment,initial_loss=loss1,next_update_bitwise_equal=True,nonempty_optimizer=True,gradient_horizon=32))
save('optimizer-replay.json',dict(passed=True,checks=replay,test_evaluated=False))
arm_summaries=[]
for treatment in [False,True]:
 arm='corrected' if treatment else 'original';model,optimizer=fresh();history=[];best_state=copy.deepcopy(model.state_dict());best=1e30;best_epoch=0;best_row=None;completed=0;ep=1;cursor=0;total=0.;batches=0
 resume=R/'data/pilot-resume'/f'{arm}.pt'
 if resume.exists():
  ck=torch.load(resume,map_location=device,weights_only=False);assert ck['arm']==arm and ck['plan_sha256']==hashlib.sha256((R/'pilot-plan.json').read_bytes()).hexdigest();model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);restore_rng(ck['rng']);history=ck['history'];best_state=ck['best_state'];best=ck['best'];best_epoch=ck['best_epoch'];best_row=ck['best_row'];completed=ck['completed_epochs'];ep=ck['epoch'];cursor=ck['next_batch_offset'];total=ck['training_total'];batches=ck['batches']
 if not history:
  train_report=evaluate(model,z,train,mean,std);validation=evaluate(model,z,valid,mean,std);diagnostic=diagnostics(model,valid);best=validation['rollout']['objective'];best_row=dict(epoch=0,train=train_report,validation=validation,diagnostics=diagnostic);history=[best_row];save(f'{arm}-baseline.json',best_row)
 def pack():return dict(arm=arm,model=model.state_dict(),optimizer=optimizer.state_dict(),rng=rngstate(),history=history,best_state=best_state,best=best,best_epoch=best_epoch,best_row=best_row,completed_epochs=completed,epoch=ep,next_batch_offset=cursor,training_total=total,batches=batches,mean=mean,std=std,plan_sha256=hashlib.sha256((R/'pilot-plan.json').read_bytes()).hexdigest(),checkpoint_boundary='Completed batch; exact remaining order deterministically reconstructed; no mid-graph state')
 while ep<=PLAN['continuation_epochs_per_arm']:
  windows=[(int(n),j) for n in train.tolist() for j in range(59)];order=np.random.default_rng(3516+183+ep).permutation(len(windows))
  for off in range(cursor,len(windows),P['batch_windows']):
   cursor=off
   if time.monotonic()-start>PLAN['budget_plan']['soft_training_s']:
    checkpoint(f'{arm}-deadline.pt',pack());save('partial.json',dict(reason='soft_deadline',arm=arm,completed_epochs=completed,next_batch_offset=cursor,test_evaluated=False));raise RuntimeError('Deadline checkpoint preserved; no automatic continuation')
   batch=[windows[i] for i in order[off:off+P['batch_windows']]];ids=torch.tensor([n for n,j in batch],device=device);js=torch.tensor([j for n,j in batch],device=device);total+=train_batch(model,optimizer,ids,js,treatment);batches+=1;cursor=off+len(batch)
  tr=evaluate(model,z,train,mean,std);va=evaluate(model,z,valid,mean,std);diag=diagnostics(model,valid);assert diag['finite'] and va['rollout']['finite'] and tr['rollout']['finite'];row=dict(epoch=ep,training_window_objective=total/batches,train=tr,validation=va,diagnostics=diag);history.append(row);score=va['rollout']['objective']
  if score<best:best=score;best_epoch=ep;best_state=copy.deepcopy(model.state_dict());best_row=row
  completed=ep;save(f'{arm}-epoch{ep:03}.json',row);ep+=1;cursor=0;total=0.;batches=0;checkpoint(f'{arm}-epoch{completed:03}.pt',pack())
 model.load_state_dict(best_state);selection=dict(arm=arm,epoch=best_epoch,original_validation_objective=best,model_sha256=statehash(model.state_dict()),row=best_row);checkpoint(f'{arm}-selected.pt',dict(model=best_state,mean=mean,std=std,epoch=best_epoch,arm=arm));save(f'{arm}-selection.json',selection);arm_summaries.append(selection)
save('selection-freeze.json',dict(arms=arm_summaries,selection='Original3state full-autonomous validation objective',test_evaluated=False))
base,candidate=[x['row'] for x in arm_summaries];br=base['validation']['rollout'];cr=candidate['validation']['rollout'];bd=base['diagnostics'];cd=candidate['diagnostics'];criteria=PLAN['acceptance_all_required']
def relative_improvement(old,new,minimum):return old is not None and new is not None and old>0 and new<=old*(1-minimum)
def bounded_increase(old,new,maximum):return old is not None and new is not None and new<=old*(1+maximum)
checks=dict(startup_gas=relative_improvement(bd['startup_gas_p90_deficit'],cd['startup_gas_p90_deficit'],criteria['startup_0_to32s_gas_p90_normalized_deficit_relative_reduction_at_least']),peak_amplitude=relative_improvement(br['peak_release_MAE_kg_s'],cr['peak_release_MAE_kg_s'],criteria['gas_peak_amplitude_MAE_relative_reduction_at_least']),original_objective=bounded_increase(br['objective'],cr['objective'],criteria['original_validation_objective_relative_increase_at_most']),each_state_MAE=all(bounded_increase(x,y,criteria['full_rollout_each_state_MAE_relative_increase_at_most']) for x,y in zip(br['physical_MAE_by_feature'],cr['physical_MAE_by_feature'])),quiet_MAE=bd['quiet_physical_MAE'] is not None and cd['quiet_physical_MAE'] is not None and all((y-x)/s<=criteria['quiet_state_MAE_absolute_increase_at_most_in_physical_encoding_scale_units'] for x,y,s in zip(bd['quiet_physical_MAE'],cd['quiet_physical_MAE'],scale.cpu().tolist())),finite=bd['finite'] and cd['finite'])
save('comparison.json',dict(passed=all(checks.values()),checks=checks,selections=arm_summaries,test_evaluated=False,scope=PLAN['comparison_scope']))
save('complete.json',dict(passed=True,experiment_succeeded=True,repair_acceptance_passed=all(checks.values()),arms_completed=len(arm_summaries),epochs_per_arm=12,test_evaluated=False,manifest=manifest))
