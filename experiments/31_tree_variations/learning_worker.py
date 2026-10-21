"""Geometry baseline then bounded recurrent correction; freeze fresh predictions before FDS."""
from pathlib import Path
import json,time,io,copy,hashlib,tarfile,traceback,urllib.request,urllib.parse,os
import numpy as np,torch
from original_cnn import ROOT,load,cond,encode,decode,prediction
from geometry_model import GeometryCNN,features
from sequence import Sequence
from previous_loss import objective
from snapshot_evaluation import metrics
PREFIX='variation31/gpu01/';BUCKET='tmrw-wildfire-20261015-trial'
def upload(name,data):
 req=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'});token=json.load(urllib.request.urlopen(req,timeout=20))['access_token'];u='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+name,safe='');urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'},method='POST'),timeout=180).read()
def main():
 assert torch.cuda.is_available();torch.set_num_threads(4);torch.manual_seed(3101);rng=np.random.default_rng(3101);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 cs=json.loads((ROOT/'cases.json').read_text());assert len(cs)==48 and all(c['split'] in ['train','validation'] for c in cs);tests=json.loads((ROOT/'fresh-tests.json').read_text());assert len(tests)==2 and all(c['split']=='test' for c in tests);geoms=dict(np.load(ROOT/'data/geometries.npz'));arrays={c['case']:load(c) for c in cs};materials={c['case']:dict(np.load(ROOT/'data'/(c['case']+'-material.npz'))) for c in cs};train=[c for c in cs if c['split']=='train'];val=[c for c in cs if c['split']=='validation'];pools=[[c for c in train if c['new_geometry']==v] for v in [False,True]]
 def condition(c,t):return torch.from_numpy(np.concatenate([cond(c,t),np.repeat(features(geoms[c['case']])[None],len(t),axis=0)],1)).cuda()
 def tensortruth(c,k):a,t=arrays[c['case']];return torch.from_numpy(encode(a[k:k+1],c['wind_speed'])).cuda()
 base=GeometryCNN().cuda();base.warm_start(torch.load(ROOT/'data/models/previous.pt',map_location='cuda',weights_only=True));opt=torch.optim.AdamW(base.parameters(),lr=.0001,weight_decay=1e-5)
 @torch.no_grad()
 def basefields(c,t):return torch.cat([base(condition(c,t[k:k+2])) for k in range(0,len(t),2)])
 def fieldscore(c,b):
  a,t=arrays[c['case']];scores=[]
  for k in range(0,len(t),2):scores.append(float(objective(b[k:k+2],torch.from_numpy(encode(a[k:k+2],c['wind_speed'])).cuda())))
  return float(np.mean(scores))
 def aggregate(rows):return float(np.mean([np.mean([score for c,score in rows if c['new_geometry']==v]) for v in [False,True]]))
 def assess_base():
  with torch.no_grad():return aggregate([(c,fieldscore(c,basefields(c,arrays[c['case']][1]))) for c in val])
 best=assess_base();state=copy.deepcopy(base.state_dict());selected=0;history=[dict(step=0,score=best)];started=time.monotonic()
 def snapshot_step():
  pool=pools[int(rng.integers(2))];c=pool[int(rng.integers(len(pool)))];a,t=arrays[c['case']];ix=rng.integers(len(t),size=2);v=base(condition(c,t[ix]));y=torch.from_numpy(encode(a[ix],c['wind_speed'])).cuda();loss=objective(v,y);assert torch.isfinite(loss);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(base.parameters(),5);opt.step()
 resume_path=os.environ.get('RESUME_CHECKPOINT');resume=torch.load(resume_path,map_location='cuda',weights_only=False) if resume_path else None
 start_step=0
 if resume and resume['stage']=='snapshot':
  base.load_state_dict(resume['model']);opt.load_state_dict(resume['optimizer']);state=resume['best_state'];best=resume['best'];selected=resume['selected'];history=resume['history'];start_step=resume['step'];rng.bit_generator.state=resume['numpy_rng'];torch.set_rng_state(resume['cpu_rng'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in resume['cuda_rng']])
 if resume and resume['stage']=='hybrid':state=resume['snapshot'];start_step=3200
 for i in range(start_step+1,3201):
  snapshot_step()
  if i%800==0:
   score=assess_base();history.append(dict(step=i,score=score));print('GEOMETRY_BASELINE',i,score,flush=True)
   if score<best:best=score;state=copy.deepcopy(base.state_dict());selected=i
  if i%400==0:
   b=io.BytesIO();torch.save(dict(stage='snapshot',model=base.state_dict(),optimizer=opt.state_dict(),step=i,best_state=state,best=best,selected=selected,history=history,numpy_rng=rng.bit_generator.state,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),b);upload('snapshot-checkpoint-%04d.pt'%i,b.getvalue())
 base.load_state_dict(state);base.eval();base_report=dict(history=history,selected_step=selected,fit_seconds=time.monotonic()-started,steps=3200,frames_per_step=2,sampling='50% old geometry, 50% new geometry; uniform configurations within each');buf=io.BytesIO();torch.save({k:v.cpu() for k,v in state.items()},buf);upload('geometry_snapshot.pt',buf.getvalue());(ROOT/'data/models/geometry_snapshot.pt').write_bytes(buf.getvalue())
 for p in base.parameters():p.requires_grad_(False)
 seq=Sequence(geoms[cs[0]['case']]).cuda();seq.load_state_dict(torch.load(ROOT/'data/models/sequence_stage1.pt',map_location='cuda',weights_only=True));torch.nn.init.zeros_(seq.out.weight);torch.nn.init.zeros_(seq.out.bias);sopt=torch.optim.AdamW(seq.parameters(),lr=.0001,weight_decay=1e-5)
 def configure(c):seq.set_geometry(geoms[c['case']]);return seq.source(c)
 @torch.no_grad()
 def rollout(c,t,ablate=False):
  src=configure(c);b=basefields(c,t);p,m,tp,h=seq.initialize(c);out=[p[0].clone()]
  for k in range(len(t)-1):
   if ablate:p=b[k:k+1];m=(seq.initial_mass>0).float();tp=torch.zeros_like(m);h=None
   p,m,tp,h=seq(p,m,tp,h,c,float(t[k]),src,baseline=b[k+1:k+2]);out.append(p[0].clone())
  return torch.stack(out)
 def assess_seq():return aggregate([(c,fieldscore(c,rollout(c,arrays[c['case']][1]))) for c in val])
 sbest=assess_seq();sstate=copy.deepcopy(seq.state_dict());sselected=0;shistory=[dict(step=0,score=sbest)];sstart=time.monotonic()
 def trajectory_step():
  pool=pools[int(rng.integers(2))];c=pool[int(rng.integers(len(pool)))];a,t=arrays[c['case']];src=configure(c);b=basefields(c,t);p,m,tp,h=seq.initialize(c);mask=(seq.initial_mass>0).float();sopt.zero_grad();block=0.;total=0.;truthm=materials[c['case']]
  for k in range(len(t)-1):
   p,m,tp,h=seq(p,m,tp,h,c,float(t[k]),src,baseline=b[k+1:k+2]);ym=torch.from_numpy(truthm['mass'][k+1:k+2]).cuda()/seq.initial_mass.clamp_min(1e-8);yt=torch.asinh((torch.from_numpy(truthm['temperature'][k+1:k+2]).cuda()-20)/100);loss=objective(p,tensortruth(c,k+1))+.05*((m-ym).square()*mask).sum()/mask.sum()+.02*((tp-yt).square()*mask).sum()/mask.sum();assert torch.isfinite(loss);block=block+loss/90;total+=float(loss.detach())/90
   if (k+1)%8==0 or k==len(t)-2:
    block.backward();block=0.;p=p.detach();m=m.detach();tp=tp.detach();h=h.detach()
  torch.nn.utils.clip_grad_norm_(seq.parameters(),1);sopt.step();return total
 def seqcheckpoint(i):
  z=io.BytesIO();torch.save(dict(stage='hybrid',snapshot=base.state_dict(),model=seq.state_dict(),optimizer=sopt.state_dict(),step=i,best_state=sstate,best=sbest,selected=sselected,history=shistory,numpy_rng=rng.bit_generator.state,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),z);return z.getvalue()
 def restore(data):
  d=torch.load(io.BytesIO(data),map_location='cuda',weights_only=False);seq.load_state_dict(d['model']);sopt.load_state_dict(d['optimizer']);rng.bit_generator.state=d['numpy_rng'];torch.set_rng_state(d['cpu_rng'].cpu());torch.cuda.set_rng_state_all([v.cpu() for v in d['cuda_rng']])
 start_trajectory=0
 if resume and resume['stage']=='hybrid':
  restore(Path(resume_path).read_bytes());sstate=resume['best_state'];sbest=resume['best'];sselected=resume['selected'];shistory=resume['history'];start_trajectory=resume['step']
 for i in range(start_trajectory+1,161):
  loss=trajectory_step()
  if i%40==0:
   score=assess_seq();shistory.append(dict(step=i,score=score,training_trajectory_loss=loss));print('FULL_ROLLOUT_HYBRID',i,score,flush=True)
   if score<sbest:sbest=score;sstate=copy.deepcopy(seq.state_dict());sselected=i
  if i%20==0:
   z=seqcheckpoint(i);upload('hybrid-checkpoint-%03d.pt'%i,z)
   if i==20:
    trajectory_step();expected={k:v.detach().cpu().clone() for k,v in seq.state_dict().items()};restore(z);trajectory_step();delta=max(float((v.detach().cpu()-expected[k]).abs().max()) for k,v in seq.state_dict().items());assert delta<1e-5,delta;restore(z);upload('resume-check.json',json.dumps({'max_weight_difference':delta,'scope':'next full training trajectory after optimizer/RNG reload'}).encode())
 seq.load_state_dict(sstate);buf=io.BytesIO();torch.save({k:v.cpu() for k,v in sstate.items()},buf);upload('hybrid.pt',buf.getvalue());(ROOT/'data/models/hybrid.pt').write_bytes(buf.getvalue());sreport=dict(history=shistory,selected_step=sselected,fit_seconds=time.monotonic()-sstart,trajectories=160,frames_per_trajectory=90,gradient_truncation_steps=8,sampling=base_report['sampling'],architecture='Geometry snapshot prior plus bounded +/-0.5 encoded-unit recurrent correction; not a standalone learned solver')
 rows=[];timing={};histories=[];(ROOT/'data/predictions').mkdir(exist_ok=True)
 for c in cs+tests:
  t=np.arange(0,181,2,dtype=float) if c in tests else arrays[c['case']][1];forecasts={}
  for name in (['snapshot','hybrid','state_reset_ablation'] if c in tests else ['snapshot','hybrid']):
   start=time.perf_counter();out=basefields(c,t) if name=='snapshot' else rollout(c,t,ablate=(name=='state_reset_ablation'));torch.cuda.synchronize();timing.setdefault(name,[]).append(time.perf_counter()-start);forecasts[name]=decode(out.cpu().numpy(),c['wind_speed']);assert np.isfinite(forecasts[name]).all()
   if c in tests or c in [x for x in val if x['new_geometry']]:np.savez_compressed(ROOT/'data/predictions'/(name+'_'+c['case']+'.npz'),fields=forecasts[name],time=t)
   if c not in tests:
    a,_=arrays[c['case']];rows.append(dict(case=c['case'],split=c['split'],new_geometry=c['new_geometry'],model=name,**metrics(np.array(a),forecasts[name],t)));histories.append(dict(case=c['case'],model=name,time_s=t.tolist(),truth_heat_kW=(a[:,1].sum((1,2,3))*.125).tolist(),predicted_heat_kW=(forecasts[name][:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=a[:,0].max((1,2,3)).tolist(),predicted_peak_C=forecasts[name][:,0].max((1,2,3)).tolist()))
  if c in [x for x in val if x['new_geometry']]:
   ab=decode(rollout(c,t,ablate=True).cpu().numpy(),c['wind_speed']);a,_=arrays[c['case']];rows.append(dict(case=c['case'],split=c['split'],new_geometry=True,model='state_reset_ablation',**metrics(np.array(a),ab,t)))
  print('EVALUATED_OR_FROZEN',c['case'],flush=True)
 result=dict(input_hashes={'base':json.loads((ROOT/'input-hashes.json').read_text()),'learning':json.loads((ROOT/'learning-hashes.json').read_text())},snapshot_training=base_report,hybrid_training=sreport,rows=rows,histories=histories,inference_median_s={k:float(np.median(v)) for k,v in timing.items()},new_cases=10,old_cases=38,fresh_test_outputs_accessed=False);(ROOT/'results/learning.json').write_text(json.dumps(result,indent=2))
 paths=[ROOT/'data/models/geometry_snapshot.pt',ROOT/'data/models/hybrid.pt',*list((ROOT/'data/predictions').glob('*.npz')),ROOT/'sequence.py',ROOT/'geometry_model.py',ROOT/'learning_worker.py',ROOT/'fresh-tests.json'];freeze=dict(created_unix=time.time(),cases=[c['case'] for c in tests],files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},test_deck_hashes={c['case']:c['deck_sha256'] for c in tests},rule='Predictions and weights frozen before launching fresh test FDS; no test outputs accessed');(ROOT/'results/prediction-freeze.json').write_text(json.dumps(freeze,indent=2))
 with tarfile.open(ROOT/'learning-outputs.tar','w') as tar:
  for p in paths+[ROOT/'results/learning.json',ROOT/'results/prediction-freeze.json']:tar.add(p,arcname=str(p.relative_to(ROOT)))
 raw=(ROOT/'learning-outputs.tar').read_bytes();upload('learning.json',json.dumps(result).encode());upload('prediction-freeze.json',json.dumps(freeze).encode());upload('outputs.tar',raw);upload('complete.json',json.dumps({'success':True,'output_sha256':hashlib.sha256(raw).hexdigest()}).encode())
if __name__=='__main__':
 try:main()
 except BaseException:
  msg=traceback.format_exc();print(msg,flush=True)
  try:upload('error.txt',msg.encode())
  except Exception:pass
  raise
