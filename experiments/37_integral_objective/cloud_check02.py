"""Cloud-only timing and next-update replay of the actual generated loss."""
from pathlib import Path
import math,time,io,json,torch
src=Path(__file__).with_name('worker.py').read_text()
exec(compile(src.split('checks=[]')[0],__file__,'exec'))
rotation=meta['rotations'][0];train=torch.tensor(rotation['train'],device=device);valid=torch.tensor(rotation['validation'],device=device)
mean,std=normalize_fit(raw,train,config,scale);z=(torch.asinh(raw/scale)-mean)/std
model=Transition('gated').to(device);model.set_normalization(mean,std)
replica_weights=torch.zeros(2080,device=device)
for n in train.tolist():replica_weights[n]=1/int((config[train]==config[n]).sum())
fragment=src[src.index('   left_error='):src.index("assert bool(torch.isfinite(loss)),f'Nonfinite")]
import textwrap
loss_code=compile(textwrap.dedent(fragment),'<actual-training-loss>','exec')
def batch_loss(h,offset=0):
 ids=train[(torch.arange(256,device=device)+offset)%len(train)];js=(torch.arange(256,device=device)*7)%(91-h)
 hist=history_at(z,ids,js);memory=prefix_memory(model,z,ids,js)
 ns=dict(globals(),ids=ids,js=js,h=h,hist=hist,memory=memory)
 exec(loss_code,ns);return ns['loss'],ns['state_per_window'].mean().detach(),ns['gate_per_window'].mean().detach()
# Training-only timing, backward but no parameter updates.
rates={};components={}
for h in (1,8,16,32):
 model.train();elapsed=[]
 for rep in range(4):
  model.zero_grad(set_to_none=True);torch.cuda.synchronize();t=time.monotonic();loss,st,ga=batch_loss(h,rep*256);loss.backward();torch.cuda.synchronize();elapsed.append(time.monotonic()-t)
  assert torch.isfinite(loss) and all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
 rates[h]=max(elapsed[1:]);components[h]=dict(state=float(st),gate=float(ga),weighted_gate=float(.1*ga))
t=time.monotonic();evaluate(model,z,train,mean,std);evaluate(model,z,valid,mean,std);torch.cuda.synchronize();evaluation=time.monotonic()-t
projection=2*sum(count*(math.ceil(len(train)*(91-h)/256)*rates[h]+evaluation) for h,count in [(1,20),(8,20),(16,20),(32,340)])+400*2+1800
save('timing-check.json',dict(passed=projection<56000,seconds_by_horizon=rates,components=components,evaluation_seconds=evaluation,conservative_400_epoch_seconds=projection,test_evaluated=False))
assert projection<56000,'Measured worst-case timing exceeds reserved deadline; no fitting launched'
# One actual-loss update, serialization, then an identical next update after restoring.
model.train();opt=torch.optim.AdamW(model.parameters(),lr=P['learning_rate'],weight_decay=1e-4)
def update():
 opt.zero_grad(set_to_none=True);loss,_,_=batch_loss(32);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step();return loss.detach().clone()
update();buf=io.BytesIO();torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),rng=rngstate()),buf)
expected=update();expected_state={k:v.clone() for k,v in model.state_dict().items()};expected_opt=opt.state_dict()
buf.seek(0);ck=torch.load(buf,map_location=device,weights_only=False);model=Transition('gated').to(device);model.load_state_dict(ck['model']);opt=torch.optim.AdamW(model.parameters(),lr=P['learning_rate'],weight_decay=1e-4);opt.load_state_dict(ck['optimizer']);restore_rng(ck['rng']);actual=update()
assert torch.equal(expected,actual) and all(torch.equal(v,model.state_dict()[k]) for k,v in expected_state.items())
for key,state in expected_opt['state'].items():
 for name,value in state.items():
  other=opt.state_dict()['state'][key][name]
  assert torch.equal(value.cpu(),other.cpu()) if torch.is_tensor(value) else value==other
save('optimizer-resume-check.json',dict(passed=True,actual_loss=True,nonempty_optimizer=True,next_update_bitwise=True,test_evaluated=False,probe_weights_discarded=True))
