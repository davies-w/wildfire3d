from pathlib import Path
import json,shutil,yaml
root=Path('/Users/wdavies/pi/wildfire3d');parent=root/'experiments/35_surrogate_diagnostics';old=parent/'attempt04';a=parent/'attempt05';a.mkdir();(a/'data/resume').mkdir(parents=True);(a/'data/initial').mkdir();(a/'results').mkdir()
for p in old.glob('*.py'):
 if p.name=='audit_output_clamps.py':continue
 (a/p.name).write_text(p.read_text().replace('diag35-04','diag35-05').replace('gpu35-diag04','gpu35-diag05').replace('diagnostics35/attempt04','diagnostics35/attempt05'))
for n in ['cases.json','groups.json','replica-time-audit.json','input-sources.json','restore-manifest.json']:(a/n).write_text((old/n).read_text().replace('diagnostics35/attempt04','diagnostics35/attempt05'))
shutil.copy2(old/'data/geometries.npz',a/'data/geometries.npz');shutil.copy2(old/'data/collected/restart-epoch-080.pt',a/'data/initial/single.pt')
plan=json.loads((old/'coverage-plan.json').read_text());plan['epochs']={'clamped':80,'raw_hrr':80};plan['learning_rates']={'both':'cosine3e-4 to1e-5 over80additionalepochs'};plan['schedule_seed_offset']=160;plan['scope']='Matched HRR output-clamp diagnostic from attempt04 restart epoch80, identical weights/optimizer and physical predictions. One TRAINtrajectory,32developmentvalidationconfigs40trajectories. Encoded training objective differs by HRR clamp only; common normalized evaluation uses clamped HRR for both. No pristine test.';(a/'coverage-plan.json').write_text(json.dumps(plan,indent=2))
(a/'raw_hrr_model.py').write_text('''"""Remove only HRR clamp from encoded model outputs used by training."""
import torch
from torch.nn import functional as F
from geometry_model import GeometryCNN
from original_cnn import CNN
class RawHRRGeometryCNN(GeometryCNN):
 def forward(self,c):
  out=CNN.forward(self,c);raw=20+100*torch.sinh(out[:,:1].clamp(-5,5));te=torch.asinh((6+F.softplus(raw-6,beta=.5)-20)/100)
  return torch.cat([te,out[:,1:2],out[:,2:5],out[:,5:6].clamp(0,10)],1)
def common_encoded(p):return torch.cat([p[:,:1],p[:,1:2].clamp(0,10),p[:,2:]],1)
''')
p=a/'worker.py';s=p.read_text().replace('from diagnostic_model import OracleCNN','from diagnostic_model import OracleCNN\nfrom raw_hrr_model import RawHRRGeometryCNN,common_encoded');s=s.replace("initial_checkpoint['arm']=='single'","initial_checkpoint['arm']=='restart'");s=s.replace('m=GeometryCNN().cuda();m.load_state_dict(base_state)',"m=(RawHRRGeometryCNN() if arm=='raw_hrr' else GeometryCNN()).cuda();m.load_state_dict(base_state)")
s=s.replace("['low','restart']","['clamped','raw_hrr']").replace("rate=1e-5 if arm=='low' else 3e-4","rate=3e-4").replace('3501+80+epoch','3501+160+epoch')
s=s.replace("err=torch.zeros(6,device='cuda');windows=","err=torch.zeros(6,device='cuda');objective_err=torch.zeros(6,device='cuda');windows=")
s=s.replace("err+=((p-y).abs()/sc).mean((2,3,4)).sum(0);b=physical(p,c['wind_speed'])","objective_err+=((p-y).abs()/sc).mean((2,3,4)).sum(0);p=common_encoded(p);err+=((p-y).abs()/sc).mean((2,3,4)).sum(0);b=physical(p,c['wind_speed'])")
s=s.replace("normalized_MAE=float(err.mean()/n),channel_normalized", "normalized_MAE=float(err.mean()/n),objective_normalized_MAE=float(objective_err.mean()/n),channel_normalized")
start=s.index(" baseline=make('eight');oracle=make('oracle');c=train[0]");end=s.index(" for arm in ['clamped','raw_hrr']:",start)
s=s[:start]+''' baseline=make('clamped');unclamped=make('raw_hrr');c=next(c for c in train if c['case']==plan['single_case'])
 with torch.no_grad():
  aa=forward(baseline,'clamped',c,0,1);bb=forward(unclamped,'raw_hrr',c,0,1)
  assert torch.equal(common_encoded(aa),common_encoded(bb));assert torch.equal(physical(aa,c['wind_speed']),physical(bb,c['wind_speed']))
 grads={}
 for label,model in [('clamped',baseline),('raw_hrr',unclamped)]:
  p=forward(model,label,c,0,1);grad=torch.autograd.grad(p[:,1].mean(),model.out.bias)[0];grads[label]=grad.detach().cpu().tolist()
 assert grads['clamped'][1]==0 and abs(grads['raw_hrr'][1])>.99
 upload('matched-initialization.json',json.dumps(dict(passed=True,initial_physical_prediction_exact=True,initial_common_encoded_prediction_exact=True,direct_HRR_bias_derivative=grads,base_weights_sha256=digest(baseline))).encode());del baseline,unclamped;torch.cuda.empty_cache()
''' +s[end:];p.write_text(s)
p=a/'analyze.py';s=p.read_text().replace("['low','restart']","['clamped','raw_hrr']").replace('Matched single-trajectory learning-rate comparison','Matched single-trajectory HRR-clamp comparison');s=s.replace("assert initial_rows[0]==initial_rows[1], 'Initial metrics differ'","assert [{k:v for k,v in row.items() if k!='objective_normalized_MAE'} for row in initial_rows[0]]==[{k:v for k,v in row.items() if k!='objective_normalized_MAE'} for row in initial_rows[1]], 'Initial common/physical metrics differ'")
s=s.replace("fitting_target_met=summary[0]['final']<=.05)","fitting_target_met=summary[0]['final']<=.05,objective_train_curve=[dict(epoch=r['epoch'],value=mean([v for v in r['rows'] if v['split']=='train'],lambda v:v['objective_normalized_MAE'])) for r in records])");p.write_text(s)
p=a/'restore_inputs.py';s=p.read_text().replace("'attempt03'","'attempt04'").replace("attempt03/data/collected/single-epoch-080.pt","attempt04/data/collected/restart-epoch-080.pt");p.write_text(s)
p=a/'validate.py';s=p.read_text();s += '''
from raw_hrr_model import RawHRRGeometryCNN,common_encoded
state=torch.load(R/'data/initial/single.pt',map_location='cpu',weights_only=False)
assert state['arm']=='restart' and state['epoch']==80
m=GeometryCNN();m.load_state_dict(state['model']);o=RawHRRGeometryCNN();o.load_state_dict(state['model'])
from geometry_model import features
from original_cnn import cond
c=next(c for c in cs if c['case']==plan['single_case']);t=np.array([0.]);g=z[c['case']]
x=torch.from_numpy(np.concatenate([cond(c,t),features(g)[None],np.full((1,1),(c['moisture']-.12)/.18,np.float32)],axis=1))
a=m(x);b=o(x);assert torch.equal(common_encoded(a),common_encoded(b))
ga=torch.autograd.grad(a[:,1].mean(),m.out.bias)[0];gb=torch.autograd.grad(b[:,1].mean(),o.out.bias)[0]
assert ga[1]==0 and abs(float(gb[1]))>.99
p=R/'results/preflight.json';d=json.loads(p.read_text());d.update(checkpoint_arm='restart',common_prediction_exact=True,clamped_HRR_bias_derivative=float(ga[1]),raw_HRR_bias_derivative=float(gb[1]));p.write_text(json.dumps(d,indent=2))
print('Matched output/gradient diagnostic passed; no optimizer update')
''';p.write_text(s)
d=yaml.safe_load((old/'dvc.yaml').read_text());d['stages'].pop('output_clamp_audit');d['stages']['inputs']['deps']=[v.replace('../attempt03/','../attempt04/').replace('single-epoch-080.pt','restart-epoch-080.pt') for v in d['stages']['inputs']['deps']];d['stages']['package']['deps'].append('raw_hrr_model.py');(a/'dvc.yaml').write_text(yaml.safe_dump(d,sort_keys=False))
(a/'README.md').write_text('''# Experiment35 attempt05: isolate the heat-release training clamp

Two copies of attempt04 restart epoch80 weights AND optimizer,80additional full epochs each on x32_033_s0. Both cosine3e-4 to1e-5, same deterministic windows3501+160+epoch,91frames once per epoch. Control clamps encoded HRR[0,10] before unchanged equal-channel standardized MAE; raw_hrr omits ONLY this clamp in the training objective. Temperature/radiation transforms unchanged. Physical decoding still clamps HRR nonnegative. Initial common encoded and physical predictions match exactly; encoded objective intentionally differs. Eight original TRAINcases still define normalization; only one case optimized. All32previously examined development validation configurations40trajectories plus fulltrain evaluated EVERYepoch. Common normalized evaluation clamps HRR for both; separately report raw objective. No auxiliary losses/newFDS/laptoptraining.

Hypothesis: hardclamp creates zero direct HRR gradient in negative region. Actual checkpoint CPU and CUDA direct output-bias derivative checks required; shared weights still receive other-channel gradients. Removing obstruction need not yield fidelity: sparse MAE can still favor nearzero and model may underfit. Compare physical HRR/hotT/radiation/airflow, not just aggregate. No pristine test or capacity-limit claim.

Reserve full4.50USD before paid action, cumulative92.60/100 retaining failed attempts/archive; invoice unknown. Estimated40–70min,20minqueue90mintask95minVM120minabsolute. Uploaded checkpoints every250updates/eachepoch preserve optimizer/scheduler/RNG/scheduleposition/aggregates. No automatic paid retry. Fresh SHAverified96inputs avoid age1expiry; bucket policy unchanged. Collector removes exact temporary grant and verifies VM/job/disks empty. DVC stages execute submit/collect/analysis; preserve all code/workflowgenerator/checkpoints in Git/DVC/public archive.

Generic3mwideconicalcrowns4/6/8/10mabove2m,1600weightedparticles,.5m24x16x16m180s,artificial1500C20s source,no trunks/buildings/embers,sixgasfieldsnotgroundtemperature. Snapshotgeometrysummaries,no evolvingfuelstate;3framebatches notrecurrence. No physicalvalidation.
''')
shutil.copy2('/tmp/make35_05.py',root/'scripts/prepare_surrogate_diagnostics35_attempt05.py')
