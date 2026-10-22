"""Three GeometryCNN copies from identical weights/optimizer and schedule."""
from worker_base import *
from matched_losses import objective_for

def main():
 assert torch.cuda.is_available();torch.set_num_threads(4)
 cs=json.loads((R/'cases.json').read_text());assert all(c['split'] in ['train','validation'] for c in cs)
 geoms=dict(np.load(R/'data/geometries.npz'));arrays={c['case']:load(c) for c in cs};train=[c for c in cs if c['split']=='train'];rows=[];reports={};started=time.monotonic()
 saved=torch.load(R/'data/resume/current.pt',map_location='cuda',weights_only=False);assert saved['step']==6000
 rng=np.random.default_rng(3308);schedule=[]
 for step in range(2500):
  c=train[int(rng.integers(len(train)))];a,t=arrays[c['case']];lo,hi=[(0,10),(10,30),(30,len(t)-2)][step%3];schedule.append((c,int(rng.integers(lo,max(lo+1,hi)))))
 def evaluate(m,arm,tag):
  out=[];m.eval()
  with torch.no_grad():
   from original_cnn import decode
   for c in cs:
    a,t=arrays[c['case']];pp=[predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda').cpu().numpy() for k in range(0,len(t),3)]
    out.append(dict(arm=arm,stage=tag,case=c['case'],split=c['split'],**metrics(np.array(a),decode(np.concatenate(pp),c['wind_speed']),t)))
  m.train();return out
 initial_hash=None
 for arm in ['control','physical_low','physical_high']:
  torch.manual_seed(3308);m=GeometryCNN().cuda();m.load_state_dict(saved['model']);opt=torch.optim.AdamW(m.parameters(),lr=1e-4,weight_decay=1e-5);opt.load_state_dict(saved['optimizer']);start_step=0
  # Optional separately-budgeted recovery uses this arm's uploaded checkpoint.
  resume=R/'data/resume'/f'{arm}.pt'
  if resume.exists():
   state=torch.load(resume,map_location='cuda',weights_only=False);assert state['arm']==arm and state['schedule_seed']==3308;m.load_state_dict(state['model']);opt.load_state_dict(state['optimizer']);start_step=state['step'];torch.set_rng_state(state['cpu_rng'].cpu());torch.cuda.set_rng_state_all([x.cpu() for x in state['cuda_rng']])
  digest=hashlib.sha256(b''.join(p.detach().cpu().numpy().tobytes() for p in m.parameters())).hexdigest()
  if start_step==0:
   if initial_hash is None:initial_hash=digest
   assert digest==initial_hash
  rows+=evaluate(m,arm,'initial');c,k=schedule[min(start_step,2499)];a,t=arrays[c['case']]
  with torch.no_grad():before=predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda').clone()
  buf=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict()),buf);buf.seek(0);check=torch.load(buf,map_location='cuda',weights_only=False);m.load_state_dict(check['model']);opt.load_state_dict(check['optimizer'])
  with torch.no_grad():assert torch.equal(before,predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda'))
  upload(arm+'-resume-check.json',json.dumps(dict(passed=True,start_step=start_step,initial_weights_sha256=digest)).encode());history=[];armstart=time.monotonic()
  for step,(c,k) in enumerate(schedule,1):
   if step<=start_step:continue
   a,t=arrays[c['case']];p=predict(m,arm,c,t[k:k+3],geoms[c['case']],'cuda');y=torch.tensor(encode(a[k:k+3],c['wind_speed']),device='cuda');ambient=torch.tensor(np.array(a[0,5]),device='cuda');loss=objective_for(arm,p,y,ambient);assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),5);opt.step()
   if step%500==0:
    history.append(dict(step=step,loss=float(loss.detach()),elapsed_s=time.monotonic()-armstart));buf=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),step=step,arm=arm,schedule_seed=3308,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),buf);upload(f'{arm}-checkpoint-{step}.pt',buf.getvalue());print(arm,step,float(loss.detach()),flush=True)
  rows+=evaluate(m,arm,'final');reports[arm]=dict(history=history,elapsed_s=time.monotonic()-armstart);upload(arm+'-results.json',json.dumps(dict(rows=[x for x in rows if x['arm']==arm],training=reports[arm])).encode());del m,opt;torch.cuda.empty_cache()
 raw=json.dumps(dict(rows=rows,training=reports,elapsed_s=time.monotonic()-started,scope='Matched saved current6000 weights/optimizer; 2500 additional updates each; 12 strength-stratified train/8 development-validation configs. Three-frame radiation proxy is not full-history dose or recurrence.',input_hashes=json.loads((R/'hashes.json').read_text())),indent=2).encode();upload('report.json',raw);upload('complete.json',json.dumps(dict(success=True,report_sha256=hashlib.sha256(raw).hexdigest())).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
