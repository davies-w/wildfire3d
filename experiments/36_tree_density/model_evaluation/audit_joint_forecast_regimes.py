"""Fit-only regime/quiet alignment diagnosis, no gradients or parameter updates."""
from pathlib import Path
import json,sys,hashlib
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/joint-decoder-pilot02';O=R/'data/joint-decoder-pilot02-results';sys.path.insert(0,str(D))
from joint_data import JointData
from joint_decoder import JointDecoder
load=lambda p:json.loads(p.read_text());assert load(R/'results/joint-decoder-pilot02-failure-audit.json')['passed'];torch.set_num_threads(4);d=JointData(D);ids=d.roles['fit'][:128];initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);audit=load(R/'results/joint-decoder-pilot02-failure-audit.json');reports=[]
raw=d.raw[d.roles['fit']];loss_active=(raw[:,1:,2]>1e-6)|((raw[:,1:,:2]-raw[:,:-1,:2]).abs().amax(-1)>1e-5);quiet=d.labels[d.roles['fit']]==0
quiet_alignment=dict(fit_histories=len(raw),quiet_label_points=int(quiet.sum()),quiet_points_counted_active_by_loss=int((quiet&loss_active).sum()),fraction_quiet_counted_active_by_loss=float((quiet&loss_active).sum()/quiet.sum()))
with torch.inference_mode():
 for record in audit['arms']:
  arm=record['arm'];ep=record['posthoc_diagnostic_epoch'];snapshot=torch.load(O/f'{arm}-epoch{ep:03}.pt',map_location='cpu',weights_only=False);m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,arm);m.load_state_dict(snapshot['model']);m.eval();need_full=[];need_rolling=[];change_full=[];change_rolling=[];error_full=[];error_rolling=[]
  for chunk in ids.split(8):
   b=len(chunk);full=m(d.x[chunk],d.base[chunk],d.raw[chunk,0],d.times[chunk]);origin=torch.arange(75);slots=origin[:,None]+torch.arange(17)[None];times=d.times[chunk][:,slots].reshape(b*75,17);state=d.raw[chunk][:,origin].reshape(b*75,4);rolling=m(d.rx[chunk].reshape(b*75,16,46),d.rb[chunk].reshape(b*75,16,4),state,times).reshape(b,75,16,4)[:,:,-1];truth=d.raw[chunk,16:];base_full=d.base[chunk,15:];base_rolling=d.rb[chunk,:,-1]
   assert torch.equal(d.x[chunk,15:,-1],d.rx[chunk,:,-1,-1])
   need_full.append((truth-base_full).abs().mean(1));need_rolling.append((truth-base_rolling).abs().mean(1));change_full.append((full[:,15:]-base_full).abs().mean(1));change_rolling.append((rolling-base_rolling).abs().mean(1));error_full.append((full[:,15:]-truth).abs().mean(1));error_rolling.append((rolling-truth).abs().mean(1))
  avg=lambda parts:torch.cat(parts).mean(0).tolist()
  reports.append(dict(arm=arm,posthoc_epoch=ep,required_correction_MAE_full=avg(need_full),required_correction_MAE_rolling16=avg(need_rolling),actual_correction_mean_abs_full=avg(change_full),actual_correction_mean_abs_rolling16=avg(change_rolling),resulting_MAE_full=avg(error_full),resulting_MAE_rolling16=avg(error_rolling)))
out=dict(passed=True,optimizer_updates=0,fit_histories_in_regime_subset=len(ids),sample='First128frozen fit-role histories, descriptive mechanistic subset; not a population confidence interval or independent model evaluation.',same_target_times_exact=True,targets_compared='Identical target points16..90: full-origin0lead16..90 versus rolling16origins0..74.',head_feature_definition='46inputs: four encoded base outputs,32hidden values,nine known external values,absolute target time/180. No explicit lead, origin time or observed origin state enters the head banks. Interval output transform separately uses observed initial masses and local time increments.',quiet_alignment=quiet_alignment,arms=reports,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Descriptive fit-only evidence of forecast-regime and loss/metric differences. Hidden states may encode origin information implicitly; missing explicit lead is not proof of a unique cause. No confirmation/test, gradient, fitting, new selected model or deployment.')
(R/'results/joint-forecast-regime-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
