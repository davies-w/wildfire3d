"""CPU inference only: frozen test models, 16s horizons and truth-defined activity."""
import json,importlib.util
from pathlib import Path
import numpy as np,torch
R=Path(__file__).resolve().parent;torch.set_num_threads(4);out=R/'data/activity_comparison';out.mkdir(exist_ok=True)
labels=np.load(R/'data/activity_audit/labels.npz')['labels'];h=8;n=83
windows=np.stack([labels[:,j:j+h] for j in range(n)],1)
active=np.all((windows==1)|(windows==2),2);quiet=np.all(windows==0,2);weak=np.all(windows==3,2)
masks={'active':active,'quiet':quiet,'weak':weak,'transition':~(active|quiet|weak),'all':np.ones_like(active)}
results={};saved={}
for attempt,kind,name in [('attempt18','mlp','3-state MLP'),('attempt18','gru','3-state GRU'),('attempt22','scalar','4-state GRU')]:
 P=R.parent/attempt;spec=importlib.util.spec_from_file_location('net_'+attempt,P/'model.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 a=np.load(P/'data/sequences.npz');raw=torch.tensor(a['state']);times=torch.tensor(a['time']);geom=torch.tensor(a['geometry']);conf=a['configuration'];meta=json.loads((P/'schema.json').read_text());scale=torch.tensor(meta['physical_encoding_scales']);dt=times[:,1:]-times[:,:-1];on=(20-times[:,:-1]).clamp_min(0).minimum(dt)/dt;external=torch.cat([geom[:,None,:].expand(-1,90,-1),on[:,:,None],dt[:,:,None]],-1)/torch.tensor(meta['external_scales']);predall=np.zeros((520,n,raw.shape[-1]),dtype='float32');folds=[]
 with torch.inference_mode():
  for rotation in range(10):
   k=rotation*2+(kind=='gru');ids=torch.tensor(meta['rotations'][rotation]['test']);ck=torch.load(P/f'data/collected/fold{k:02}-selected.pt',map_location='cpu',weights_only=False);model=mod.Transition(kind);model.load_state_dict(ck['model']);model.eval();mean=ck['mean'];std=ck['std'];z=(torch.asinh(raw/scale)-mean)/std
   if kind=='scalar':z=(torch.asinh(raw.clone().index_fill(2,torch.tensor([4,5,6]),0)/scale)-mean)/std
   ii=ids[:,None].expand(-1,n).flatten();jj=torch.arange(n).expand(len(ids),-1).flatten();hist=z[ii[:,None],(jj[:,None]+torch.arange(-3,1)[None]).clamp_min(0)]
   memory=None
   if kind!='mlp':
    inputs=model.inputs(hist,external[ii,jj]) if kind=='scalar' else torch.cat([hist.flatten(1),external[ii,jj]],-1)
    prefix,_=model.cell(inputs.reshape(len(ids),n,-1));memory=torch.cat([torch.zeros(len(ids),1,32),prefix[:,:-1]],1).reshape(-1,32)
   pp=[]
   for off in range(0,len(ii),512):
    ci=ii[off:off+512];cj=jj[off:off+512];hh=hist[off:off+512];mm=None if memory is None else memory[off:off+512]
    for step in range(h):
     state,mm=model.step(hh,external[ci,cj+step],mm);hh=torch.cat([hh[:,1:],state[:,None]],1)
    pp.append((torch.sinh(state*std+mean)*scale).numpy())
   pred=np.concatenate(pp).reshape(len(ids),n,-1);assert np.isfinite(pred).all();predall[ids.numpy()]=pred
   truth=a['state'][ids.numpy(),h:];err=abs(pred-truth);hold=abs(a['state'][ids.numpy(),:n]-truth);fold={}
   for phase,mask in masks.items():
    mask=mask[ids.numpy()];count=mask.sum(1);keep=count>0;groups=conf[ids.numpy()[keep]]
    def agg(value):
     if not keep.any():return None
     v=(value*mask[:,:,None]).sum(1)[keep]/count[keep,None];return np.mean([v[groups==c].mean(0) for c in np.unique(groups)],0).tolist()
    fold[phase]={'model':agg(err),'baseline':agg(hold),'truth':agg(abs(truth))}
   folds.append(fold);print(name,rotation,flush=True)
 summary={}
 for phase in masks:
  usable=[f[phase] for f in folds if f[phase]['model'] is not None];m=np.mean([f['model'] for f in usable],0);b=np.mean([f['baseline'] for f in usable],0);d=np.mean([f['truth'] for f in usable],0)
  with np.errstate(invalid='ignore',divide='ignore'):sim=100*m/d;red=100*(1-m/b)
  summary[phase]={'model_mae':m[:4].tolist(),'no_change_mae':b[:4].tolist(),'mean_truth':d[:4].tolist(),'error_vs_sim_percent':sim[:4].tolist(),'reduction_vs_no_change_percent':red[:4].tolist(),'folds':len(usable)}
 # Replay existing whole-history metrics to check model reconstruction and weighting.
 reports=json.loads((P/'data/collected/report.json').read_text());ref=np.mean([t['horizons']['8']['model_MAE'] for t in reports['tests'] if t['kind']==kind],0)[:3]
 assert np.allclose(summary['all']['model_mae'][:3],ref,rtol=.003,atol=1e-5),(name,summary['all'],ref)
 results[name]=summary;saved[name.replace(' ','_')]=predall
np.savez_compressed(out/'predictions.npz',**saved)
report={'horizon_seconds':16,'summary':results,'counts':{k:int(v.sum()) for k,v in masks.items()},'definition':'Every endpoint of the eight two-second steps must be active/quiet/weak for stable classification; otherwise transition. Active includes substantial drying or fuel release, not necessarily combustion. Trailing10s labels have smoothing lag. Equal mean of available folds, configuration-balanced then replica-balanced within each fold. No four-state MLP exists. CPU inference replay agrees with original GPU whole-history MAE within0.3%. No fitting or selection.'}
(out/'report.json').write_text(json.dumps(report,indent=2));print('DONE',flush=True)
