"""Bounded CUDA sequence training and complete autonomous evaluation."""
import os,json,time,copy,io,tarfile,hashlib,subprocess,traceback,sys,urllib.request,urllib.parse
from pathlib import Path
import numpy as np,torch
from sequence import Sequence
from original_cnn import ROOT,load,encode,CNN,prediction,cond
from previous_loss import objective
from snapshot_evaluation import metrics
PREFIX='gpu30/sequence01/';BUCKET='tmrw-wildfire-20261015-trial'
def upload(name,data):
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(r,timeout=20))['access_token'];url='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+name,safe='');req=urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST');urllib.request.urlopen(req,timeout=180).read()
def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);torch.manual_seed(3001);rng=np.random.default_rng(3001);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 cs=json.loads((ROOT/'cases.json').read_text());assert len(cs)==38 and all(c['split'] in ['train','validation'] for c in cs);train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation'];arrays={c['case']:load(c) for c in cs};mats={c['case']:np.load(ROOT/'data'/(c['case']+'-material.npz')) for c in cs};m=Sequence(np.load(ROOT/'data/geometry.npy')).cuda();opt=torch.optim.AdamW(m.parameters(),lr=.0003,weight_decay=1e-5);mask=(m.initial_mass>0).float();sources={c['case']:m.source(c) for c in cs}
 def assess(cases):
  scores=[];peaks=[]
  for c in cases:
   a,t=arrays[c['case']];b,_=m.rollout(c,t);loss=[]
   for k in range(0,len(t),2):loss.append(float(objective(torch.from_numpy(encode(b[k:k+2],c['wind_speed'])).cuda(),torch.from_numpy(encode(a[k:k+2],c['wind_speed'])).cuda())))
   scores.append(float(np.mean(loss)));peaks.append(float(abs(b[:,0].max()-a[:,0].max())))
  return dict(score=float(np.mean(scores)),peak_error_C=float(np.mean(peaks)))
 def step(i):
  c=train[int(rng.integers(len(train)))];a,t=arrays[c['case']];n=1 if i<=400 else 4 if i<=1000 else 8;start=0 if i%4==0 else int(rng.integers(0,len(t)-n));start=min(start,len(t)-n-1);mat=mats[c['case']];p=torch.from_numpy(encode(a[start:start+1],c['wind_speed'])).cuda();mass=torch.from_numpy(mat['mass'][start:start+1]).cuda()/m.initial_mass.clamp_min(1e-8);temp=torch.asinh((torch.from_numpy(mat['temperature'][start:start+1]).cuda()-20)/100);h=None;loss=0.
  if start==0:p,mass,temp,h=m.initialize(c)
  for k in range(start,start+n):
   p,mass,temp,h=m(p,mass,temp,h,c,float(t[k]),sources[c['case']]);y=torch.from_numpy(encode(a[k+1:k+2],c['wind_speed'])).cuda();ym=torch.from_numpy(mat['mass'][k+1:k+2]).cuda()/m.initial_mass.clamp_min(1e-8);yt=torch.asinh((torch.from_numpy(mat['temperature'][k+1:k+2]).cuda()-20)/100);loss=loss+objective(p,y)+.1*((mass-ym).square()*mask).sum()/mask.sum()+.05*((temp-yt).square()*mask).sum()/mask.sum()
  loss=loss/n;assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(m.parameters(),1);opt.step();return float(loss.detach())
 best=float('inf');best_state=copy.deepcopy(m.state_dict());history=[];selected=0;started=time.monotonic();begin=0
 def checkpoint(i):
  b=io.BytesIO();torch.save(dict(model=m.state_dict(),optimizer=opt.state_dict(),step=i,best=best,best_state=best_state,selected=selected,history=history,numpy_rng=rng.bit_generator.state,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),b);return b.getvalue()
 def restore(data):
  d=torch.load(io.BytesIO(data),map_location='cuda',weights_only=False);m.load_state_dict(d['model']);opt.load_state_dict(d['optimizer']);rng.bit_generator.state=d['numpy_rng'];torch.set_rng_state(d['cpu_rng'].cpu());torch.cuda.set_rng_state_all([x.cpu() for x in d['cuda_rng']]);return d
 if os.environ.get('SEQUENCE_RESUME'):
  d=restore(Path(os.environ['SEQUENCE_RESUME']).read_bytes());begin=d['step'];best=d['best'];best_state=d['best_state'];selected=d['selected'];history=d['history']
 for i in range(begin+1,2401):
  loss=step(i)
  if i%400==0:
   result=assess(val);history.append(dict(step=i,training_window_loss=loss,**result));print('SEQUENCE',history[-1],flush=True)
   if result['score']<best:best=result['score'];best_state=copy.deepcopy(m.state_dict());selected=i
  if i%200==0:
   b=checkpoint(i);upload('checkpoint-%04d.pt'%i,b)
   if i==200:
    step(i+1);expected={k:v.detach().cpu().clone() for k,v in m.state_dict().items()};restore(b);step(i+1);delta=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in m.state_dict().items());assert delta<1e-5,delta;restore(b);upload('resume-check.json',json.dumps({'max_weight_difference':delta,'scope':'same-process optimizer/RNG resume, not actual preemption'}).encode())
 m.load_state_dict(best_state);report=dict(history=history,selected_step=selected,fit_seconds=time.monotonic()-started,parameters=sum(p.numel() for p in m.parameters()),train_cases=[c['case'] for c in train],validation_cases=[c['case'] for c in val]);(ROOT/'results/sequence-training.json').write_text(json.dumps(report,indent=2));buf=io.BytesIO();torch.save({k:v.cpu() for k,v in best_state.items()},buf);upload('sequence.pt',buf.getvalue());upload('sequence-training.json',json.dumps(report).encode())
 rows=[];histories=[];diagnostics=[];speeds=[]
 for c in cs:
  a,t=arrays[c['case']];start=time.perf_counter();b,mat=m.rollout(c,t);torch.cuda.synchronize();speeds.append(time.perf_counter()-start);row=dict(case=c['case'],split=c['split'],**metrics(np.array(a),b,t));truthmat=mats[c['case']]['mass'];row['material_relative_L1']=float(abs(mat-truthmat).sum()/max(truthmat.sum(),1e-8));rows.append(row);histories.append(dict(case=c['case'],split=c['split'],time_s=t.tolist(),truth_HRR_kW=(a[:,1].sum((1,2,3))*.125).tolist(),predicted_HRR_kW=(b[:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=a[:,0].max((1,2,3)).tolist(),predicted_peak_C=b[:,0].max((1,2,3)).tolist()));print('EVALUATED',c['case'],flush=True)
  if c in val[:2]:np.savez_compressed(ROOT/'data'/('sequence_'+c['case']+'.npz'),fields=b,time=t)
  if c in val:
   reset,_=m.rollout(c,t,reset_memory=True);forced=[];h=None;truthm=mats[c['case']]
   with torch.no_grad():
    for k in range(len(t)-1):
     p=torch.from_numpy(encode(a[k:k+1],c['wind_speed'])).cuda();mm=torch.from_numpy(truthm['mass'][k:k+1]).cuda()/m.initial_mass.clamp_min(1e-8);tp=torch.asinh((torch.from_numpy(truthm['temperature'][k:k+1]).cuda()-20)/100);v,_,_,h=m(p,mm,tp,h,c,float(t[k]),sources[c['case']]);y=torch.from_numpy(encode(a[k+1:k+2],c['wind_speed'])).cuda();forced.append(float(objective(v,y)))
   diagnostics.append(dict(case=c['case'],teacher_forced_one_step_objective=float(np.mean(forced)),reset_hidden_memory_metrics=metrics(np.array(a),reset,t)))
 summary={}
 for split in ['train','validation']:
  rr=[r for r in rows if r['split']==split];summary[split]={w:{k:float(np.mean([r[w][k] for r in rr if r[w][k] is not None])) if any(r[w][k] is not None for r in rr) else None for k in rr[0][w]} for w in ['all','post_source','late']}
 baseline=CNN().cuda();baseline.load_state_dict(torch.load(ROOT/'data/models/previous.pt',map_location='cuda',weights_only=True));base_scores=[]
 for c in val:
  a,t=arrays[c['case']];b=prediction(baseline,c,t);ss=[]
  for k in range(0,len(t),2):ss.append(float(objective(torch.from_numpy(encode(b[k:k+2],c['wind_speed'])).cuda(),torch.from_numpy(encode(a[k:k+2],c['wind_speed'])).cuda())))
  base_scores.append(float(np.mean(ss)))
 baseline_score=float(np.mean(base_scores))
 final=dict(snapshot_baseline_full_objective=baseline_score,selected_autonomous_validation_objective=best,rows=rows,histories=histories,summary=summary,diagnostics=diagnostics,inference_median_seconds_including_cpu_decode=float(np.median(speeds)),training=report,autonomous=True,initialization='prescribed ambient fields, material descriptor, no FDS future states');(ROOT/'results/sequence-evaluation.json').write_text(json.dumps(final,indent=2));upload('sequence-evaluation.json',json.dumps(final).encode())
 with tarfile.open(ROOT/'sequence-outputs.tar','w') as tar:
  for n in ['results/sequence-training.json','results/sequence-evaluation.json',*[str(p.relative_to(ROOT)) for p in (ROOT/'data').glob('sequence_*.npz')]]:tar.add(ROOT/n,arcname=n)
 data=(ROOT/'sequence-outputs.tar').read_bytes();upload('outputs.tar',data);upload('complete.json',json.dumps({'success':True,'sha256':hashlib.sha256(data).hexdigest()}).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
