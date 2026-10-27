"""Audit exact displayed truth and errors, including initial autonomous ramp."""
from pathlib import Path
import json,numpy as np
from summarize_undershoots import paired_condition
from diagnose_undershoots import R

def main():
 specs=[('old_gated',R.parent/'35_surrogate_diagnostics/attempt24/data/scenario_gallery',R.parent/'35_surrogate_diagnostics/attempt24/data/sequences.npz',[(3,'old_gated')]),('denser',R/'data/denser/gallery',R/'data/learning/sequences.npz',[(3,'dense_plain')]),('stride_pair',R/'data/pair-gallery',R/'data/learning/sequences.npz',[(2,'stride_plain'),(3,'stride_gated')])];out={};rows={};truth_checks=[];axis_checks=[]
 for name,folder,ap,arms in specs:
  a=np.load(ap);n=0;axis_ratios=[]
  for p in folder.glob('page-*.js'):
   s=p.read_text();records=json.loads(s[s.index(',')+1:s.rindex(')')])
   for r in records:
    i=r['index'];v=np.array(r['values']);truth=v[0];t=np.array(r['time']);assert np.array_equal(truth,a['state'][i,1:]);assert np.array_equal(t,a['time'][i,1:]);n+=1
    transformed=np.sign(v)*np.log10(1+abs(v)/np.array([.001,.01,.00001,.1]))
    span_all=np.ptp(transformed,axis=(0,1));shown=[0]+[arm for arm,label in arms];span_shown=np.ptp(transformed[shown],axis=(0,1));ratio=span_shown/np.maximum(span_all,1e-20);axis_ratios.append(ratio)
    for arm,label in arms:
     pred=v[arm];peaks=np.maximum(abs(truth).max(0),1e-12);err=truth-pred;wi=err.argmax(0);pi=truth.argmax(0);peakerr=(pred[pi,np.arange(4)]-truth[pi,np.arange(4)])/peaks
     row=dict(case=r['case'],conditions=[r['height'],round(r['water']/r['fuel'],6),r['loading'],r['wind'],r['angle']],config=int(a['configuration'][i]),worst=(np.maximum(err,0).max(0)/peaks).tolist(),worst_time=t[wi].tolist(),peak_time=t[pi].tolist(),peak_signed=peakerr.tolist(),gas_peak_bias=float((pred[:,2].max()-truth[:,2].max())/peaks[2]),gas_peak_time_offset=float(t[pred[:,2].argmax()]-t[truth[:,2].argmax()]))
     rows.setdefault(label,[]).append(row)
  truth_checks.append(dict(gallery=name,histories=n,truth_and_timestamps_exact=True))
  ratios=np.array(axis_ratios);axis_checks.append(dict(gallery=name,median_visible_to_all_symlog_span=np.median(ratios,axis=0).tolist(),fraction_charts_where_hidden_lines_expand_span_over_2x=np.mean(ratios<.5,axis=0).tolist(),note='Renderer scales against all four series even when comparison lines are off. Ratio compares simulation+enabled model span with all-series span, before identical padding.'))
 for label,rr in rows.items():
  groups={}
  for r in rr:groups.setdefault(r['config'],[]).append(r)
  pooled=[]
  for rs in groups.values():
   p={k:rs[0][k] for k in ['case','conditions']}
   for k in ['worst','worst_time','peak_time','peak_signed','gas_peak_bias','gas_peak_time_offset']:p[k]=np.mean([r[k] for r in rs],axis=0).tolist()
   pooled.append(p)
  w=np.array([r['worst'] for r in pooled]);cut=np.quantile(w,.9,axis=0);groups={}
  for k,name,vs in [(0,'height',[4,6,8,10]),(1,'moisture',[.06,.12,.18,.24,.3]),(2,'loading',[.7,1,1.3]),(3,'wind',[1,2,3,4,5]),(4,'angle',[0,45,90,135,180,225,315])]:
   groups[name]={}
   for val in vs:
    idx=[j for j,r in enumerate(pooled) if np.isclose(r['conditions'][k],val,atol=1e-5)]
    if not idx:continue
    groups[name][str(val)]=dict(n=len(idx),median_worst_under=np.median(w[idx],axis=0).tolist(),top_decile_rate=np.mean(w[idx]>=cut,axis=0).tolist())
  worst=sorted(pooled,key=lambda r:r['worst'][2],reverse=True);bad=worst[:int(np.ceil(len(worst)*.1))]
  out[label]=dict(histories=len(rr),configurations=len(pooled),top_decile_cut=cut.tolist(),conditions=groups,matched_moisture=paired_condition(pooled,1,.06,.3),matched_loading=paired_condition(pooled,2,.7,1.3),worst_gas_examples=worst[:12],top_gas_decile=dict(n=len(bad),median_peak_amplitude_bias=float(np.median([r['gas_peak_bias'] for r in bad])),median_abs_peak_time_offset_s=float(np.median([abs(r['gas_peak_time_offset']) for r in bad])),fraction_worst_error_in_initial_32s=float(np.mean([r['worst_time'][2]<=32.21 for r in bad]))))
 (R/'results/undershoot-gallery-truth-checks.json').write_text(json.dumps(truth_checks,indent=2)+'\n')
 out['scope']='Exact gallery trajectories: first 15 targets from autonomous rollout, then rolling 16-step forecasts. Median metrics weight physical configurations equally, average replicas. Initial 32-second ramp and later refreshed forecasts are mixed as in display. Undershoot is max positive(truth-prediction) / whole-history abs truth peak, not pointwise percentage. Post-hoc associations, no causal claims; marginal groups confounded. No smoothing or modeling changes.';out['truth_checks']=truth_checks;out['axis_checks']=axis_checks
 (R/'results/gallery-undershoot-diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')
 for label in rows:
  d=out[label];print(label,d['configurations'],d['top_gas_decile'])
  for k in ['moisture','loading','angle']:print(k,[(v,round(g['median_worst_under'][2],3),round(g['top_decile_rate'][2],3),g['n']) for v,g in d['conditions'][k].items()])
if __name__=='__main__':main()
