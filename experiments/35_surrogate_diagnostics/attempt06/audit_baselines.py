"""Local decoding/statistics only: frozen training cases, no optimization."""
from pathlib import Path
import json,tarfile,hashlib,shutil
import numpy as np
from fields import extract
from original_cnn import encode
R=Path(__file__).parent;source=R.parent/'attempt05';archive=R.parent.parent/'32_tree_expansion/data/cloud_archive'
cases=[c for c in json.loads((source/'cases.json').read_text()) if c['split']=='train'];manifest=json.loads((source/'restore-manifest.json').read_text());scales=np.array(json.loads((R.parent/'attempt03/data/collected/scales.json').read_text())['encoded_std'],np.float32)
rows=[];single='x32_033_s0';(R/'data/cloud').mkdir(exist_ok=True)
for c in cases:
 n=c['case']; item=next(i for i in manifest if i['target'].endswith('/'+n+'.tar.gz'));p=archive/item['archive_relative'];assert p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 with tarfile.open(p) as tar:
  for m in tar.getmembers():assert not m.name.startswith('/') and '..' not in Path(m.name).parts and not m.issym() and not m.islnk()
  tar.extractall(R/'data/cloud')
 folder=R/'data/cloud'/n;assert hashlib.sha256((folder/(n+'.fds')).read_bytes()).hexdigest()==c['deck_sha256'];extract(c)
 a=np.load(R/'data/fields'/(n+'.npy'),mmap_mode='r');t=np.load(R/'data/fields'/(n+'-time.npy'));rad=float(np.median(a[0,5]));entry={'case':n,'configuration':c['configuration'],'raw_sha256':item['sha256'],'radiation_initial_median':rad,'windows':{}}
 for window,sel in [('all',t>=0),('ignition',t<=20),('post_source',t>=22),('late',t>=120)]:
  aa=np.array(a[sel]);e=encode(aa,c['wind_speed']);masks={'hot_T_gt50C':aa[:,0]>50,'HRR_gt0':aa[:,1]>0,'HRR_gt0.01kWm3':aa[:,1]>.01,'HRR_gt1kWm3':aa[:,1]>1,'radiation_excess_gt0.1':aa[:,5]-rad>.1};v={'frames':int(sel.sum()),'occupancy':{k:float(v.mean()) for k,v in masks.items()},'baselines':{}}
  for label,rv in [('zero_radiation',0.),('initial_median_radiation',rad)]:
   raw=np.array([20,0,c['wind_speed'],0,0,rv],np.float32)[None,:,None,None,None];pred=np.broadcast_to(raw,aa.shape);ep=encode(pred,c['wind_speed']);err=abs(ep-e)/scales[None,:,None,None,None];channel=err.mean((0,2,3,4));physical=abs(pred-aa);hot=masks['hot_T_gt50C'];burn=masks['HRR_gt0.01kWm3']
   v['baselines'][label]={'channel_objective_MAE':channel.tolist(),'objective_MAE':float(channel.mean()),'channel_physical_MAE':physical.mean((0,2,3,4)).tolist(),'hot_temperature_MAE_C':float(physical[:,0][hot].mean()) if hot.any() else None,'burning_HRR_MAE_kWm3':float(physical[:,1][burn].mean()) if burn.any() else None}
  entry['windows'][window]=v
 rows.append(entry);shutil.rmtree(folder)
 if n!=single:
  for f in (R/'data/fields').glob(n+'*'):f.unlink()
 print(n,entry['windows']['post_source']['occupancy'],flush=True)
(R/'cases.json').write_text(json.dumps([c for c in cases if c['case']==single],indent=2));(R/'scales.json').write_text(json.dumps({'encoded_std':scales.tolist(),'source':'attempt03 training8 frozen scales'},indent=2))
(R/'results/baseline-audit.json').write_text(json.dumps({'training_cases':rows,'channels':['T','HRR','u','v','w','radiation'],'scales':scales.tolist(),'scope':'Eight selected TRAIN configurations only. Equal-channel encoded MAE and identical frame weighting. Ambient20C/zeroHRR/backgroundwind/zero transversevelocity; two specified constant radiation baselines. No validation/test fitting or optimizer.','aggregate':{w:{b:float(np.mean([r['windows'][w]['baselines'][b]['objective_MAE'] for r in rows])) for b in ['zero_radiation','initial_median_radiation']} for w in ['all','ignition','post_source','late']}},indent=2))
