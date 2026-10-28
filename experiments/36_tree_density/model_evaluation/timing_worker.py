"""CUDA-only matched four-state heads; confirmation remains closed until freeze."""
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
from pathlib import Path
import copy,hashlib,io,json,math,random,time
import numpy as np
import torch
from joint_decoder import JointDecoder
from context_data import ContextData as JointData
from joint_objective import objective
from context_objective import objective as physical_objective
from joint_metrics import checks,select,choose_winner
from runtime import upload

R=Path(__file__).resolve().parent;P=json.loads((R/'trial-plan.json').read_text());start=time.monotonic()
assert torch.cuda.is_available(),'Cloud CUDA required; local optimizers prohibited'
torch.set_num_threads(4);torch.use_deterministic_algorithms(True);torch.manual_seed(P['seed']);np.random.seed(P['seed']);random.seed(P['seed']);device='cuda'
d=JointData(R,device);initial=torch.load(R/'initial-decoder.pt',map_location=device,weights_only=False);calibration=json.loads((R/'loss-normalization.json').read_text());manifest={};folder=R/'results';folder.mkdir(exist_ok=True)
def save(name,value):
    payload=json.dumps(value,allow_nan=False).encode();(folder/name).write_bytes(payload);upload(name,payload);manifest[name]=hashlib.sha256(payload).hexdigest()
def checkpoint(name,value):
    f=io.BytesIO();torch.save(value,f);payload=f.getvalue();(folder/name).write_bytes(payload);upload(name,payload);manifest[name]=hashlib.sha256(payload).hexdigest()
def rngstate():return dict(torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),numpy=np.random.get_state(),python=random.getstate())
def restore_rng(r):
    torch.set_rng_state(r['torch'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in r['cuda']]);np.random.set_state(r['numpy']);random.setstate(r['python'])
def statehash(state):return hashlib.sha256(b''.join(v.detach().cpu().numpy().tobytes() for v in state.values())).hexdigest()
initial_rng=rngstate()
def make_model(arm):
    m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean']).to(device);m.load_state_dict(initial['model']);m.objective_arm=arm;return m

def fresh(arm):
    m=make_model(arm);o=torch.optim.AdamW(m.parameters(),lr=P['training']['learning_rate'],weight_decay=P['training']['weight_decay']);restore_rng(initial_rng);return m,o

def train_batch(m,o,ids,origins):
    m.train();args=d.training_batch(m,ids,origins);loss,parts=physical_objective(args[0],args[1],args[2],args[3],d.scales,d.std,*args[4:],**d.objective_metadata(ids,origins),normalization=calibration)
    if m.objective_arm=='tail_priority':loss=loss+.4*parts['under_tail']
    assert bool(torch.isfinite(loss));o.zero_grad(set_to_none=True);loss.backward();assert all(v.grad is None or bool(torch.isfinite(v.grad).all()) for v in m.parameters());assert all(v.grad is None for v in [m.w1,m.b1,m.w2,m.b2]);torch.nn.utils.clip_grad_norm_([v for v in m.parameters() if v.requires_grad],P['training']['gradient_clip_norm']);o.step();assert all(torch.equal(m.state_dict()[k],initial['model'][k]) for k in ['w1','b1','w2','b2']);return float(loss.detach())


replay=[]
for arm in P['arms']:
    m,o=fresh(arm);assert not o.state;ids=d.roles['fit'][:128];origins=torch.tensor([-1 if j%2 else j%75 for j in range(len(ids))],device=device)
    train_batch(m,o,ids,origins);snap=copy.deepcopy(dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate()));buffer=io.BytesIO();torch.save(snap,buffer);buffer.seek(0);snap=torch.load(buffer,map_location=device,weights_only=False);assert snap['optimizer']['state'];torch.cuda.synchronize();t=time.monotonic();train_batch(m,o,ids,origins);torch.cuda.synchronize();elapsed=time.monotonic()-t;expected=copy.deepcopy(m.state_dict());expected_opt=copy.deepcopy(o.state_dict());m.load_state_dict(snap['model']);o.load_state_dict(copy.deepcopy(snap['optimizer']));restore_rng(snap['rng']);train_batch(m,o,ids,origins);assert all(torch.equal(v,expected[k]) for k,v in m.state_dict().items())
    for key,value in o.state_dict()['state'].items():
        for name,v in value.items():assert torch.equal(v,expected_opt['state'][key][name]) if torch.is_tensor(v) else v==expected_opt['state'][key][name]
    replay.append(dict(arm=arm,empty_initial_optimizer=True,nonempty_restore=True,serialized_checkpoint_restore=True,next_update_bitwise_equal=True,measured_second_update_wall_s=elapsed,discarded_preflight_updates=3,mixed_full_and_rolling=True))
save('optimizer-replay.json',dict(passed=True,arms=replay,torch_version=torch.__version__,cuda_version=torch.version.cuda,device_name=torch.cuda.get_device_name(0),threads=torch.get_num_threads()));save('timing.json',dict(updates=replay,estimated_update_only_total_s=sum(x['measured_second_update_wall_s'] for x in replay)*math.ceil(len(d.roles['fit'])/128)*P['training']['epochs_per_arm'],scope='One warm second-update measurement per arm; excludes startup, scoring, checkpoint serialization/network. Deadline, not this extrapolation, bounds actual run.'))
assert not d.confirmation_open
baseline=d.score(None,d.roles['selection']);save('selection-baseline.json',baseline);save('selection-no-change.json',d.score(None,d.roles['selection'],no_change=True));selections=[]
for arm in P['arms']:
    m,o=fresh(arm);untrained=d.score(m,d.roles['selection']);save(arm+'-untrained-selection.json',untrained);rows=[dict(epoch=-1,metrics=baseline),dict(epoch=0,metrics=untrained)];best_row,accepted=select(baseline,rows,P['acceptance'],d.scales.tolist());best_state=copy.deepcopy(initial['model']);history=copy.deepcopy(rows)
    for ep in range(1,P['training']['epochs_per_arm']+1):
        rng=np.random.default_rng(P['seed']+ep);order=torch.tensor(rng.permutation(len(d.roles['fit'])),device=device);origins=torch.tensor(np.where(rng.random(len(order))<.5,-1,rng.integers(0,75,len(order))),device=device);total=0.;batches=0
        for cursor in range(0,len(order),128):
            if time.monotonic()-start>=P['budget_plan']['training_soft_cap_s']:
                checkpoint(arm+'-partial.pt',dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate(),epoch=ep,batch_cursor=cursor,case_permutation=order,origin_choices=origins,training_total=total,training_batches=batches,history=history,best_state=best_state,best_row=best_row,accepted_on_selection=accepted));save('incomplete.json',dict(experiment_complete=False,reason='training_soft_deadline',arm=arm,epoch=ep,batch_cursor=cursor,automatic_retry=False));raise SystemExit(0)
            total+=train_batch(m,o,d.roles['fit'][order[cursor:cursor+128]],origins[cursor:cursor+128]);batches+=1
        if ep%P['training']['selection_evaluation_every_epochs']==0:
            assert not d.confirmation_open;row=dict(epoch=ep,metrics=d.score(m,d.roles['selection']),mean_minibatch_training_loss=total/batches,elapsed_s=time.monotonic()-start);rows.append(row);history.append(row);save(f'{arm}-epoch{ep:03}.json',row);chosen,now_accepted=select(baseline,rows,P['acceptance'],d.scales.tolist())
            if chosen['epoch']==ep:best_state=copy.deepcopy(m.state_dict())
            best_row=chosen;accepted=now_accepted
        checkpoint(f'{arm}-epoch{ep:03}.pt',dict(model=m.state_dict(),optimizer=o.state_dict(),rng=rngstate(),epoch=ep,batch_cursor=len(order),case_permutation=order,origin_choices=origins,history=history,best_state=best_state,best_row=best_row,accepted_on_selection=accepted))
    apply_decoder=best_row['epoch']>=0;checkpoint(arm+'-selected.pt',dict(model=best_state,epoch=best_row['epoch'],arm=arm,apply_decoder=apply_decoder));selection=dict(arm=arm,row=best_row,epoch=best_row['epoch'],apply_decoder=apply_decoder,accepted_on_selection=accepted,model_sha256=statehash(best_state));save(arm+'-selection.json',selection);selections.append(selection)
winner=choose_winner(baseline,selections);save('selection-freeze.json',dict(arms=selections,winner=winner,confirmation_scored=False,test_evaluated=False,selection_rule=P['evaluation']))
# This is the first point where any confirmation scoring is allowed.
d.confirmation_open=True;confirm=d.roles['confirmation'];confirmation_baseline=d.score(None,confirm);save('confirmation-baseline.json',confirmation_baseline);save('confirmation-no-change.json',d.score(None,confirm,no_change=True));reports={}
for selection in selections:
    arm=selection['arm'];m=make_model(arm);save(arm+'-untrained-confirmation.json',d.score(m,confirm));selected=torch.load(folder/(arm+'-selected.pt'),map_location=device,weights_only=False);m.load_state_dict(selected['model']);report=d.score(m if selection['apply_decoder'] else None,confirm);save(arm+'-confirmation.json',report);ck=checks(confirmation_baseline,report,P['acceptance'],d.scales.tolist());reports[arm]=dict(metrics=report,checks=ck,accepted=all(ck.values()))
winning_checks=checks(confirmation_baseline,confirmation_baseline,P['acceptance'],d.scales.tolist()) if winner=='raw_baseline' else reports[winner]['checks'];passed=winner!='raw_baseline' and all(winning_checks.values());save('comparison.json',dict(passed=passed,winner=winner,checks=winning_checks,confirmation_baseline=confirmation_baseline,arms=reports,test_evaluated=False,scope=P['scope'],confirmation_limitation=P['partition_limitation']));save('complete.json',dict(passed=True,arms_completed=2,epochs_per_arm=P['training']['epochs_per_arm'],selection_frozen_before_confirmation=True,test_evaluated=False,repair_acceptance_passed=passed,manifest=copy.deepcopy(manifest)))
