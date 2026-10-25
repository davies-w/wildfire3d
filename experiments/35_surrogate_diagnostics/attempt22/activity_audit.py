"""Truth-only activity definitions; engineering thresholds, no model selection/fitting."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;a=np.load(R/'data/sequences.npz');s=a['state'];t=a['time'];c=a['configuration'];q=np.maximum(s[:,:,2],0);dt=np.diff(t);gas=(q[:,1:]+q[:,:-1])*.5*dt;cum=np.c_[np.zeros(len(s)),np.cumsum(gas,axis=1)];j=np.arange(1,91);k=np.maximum(j-5,0);elapsed=t[:,j]-t[:,k]
fuel=(cum[:,j]-cum[:,k])/.75/s[:,0,1,None]/elapsed
water=np.maximum(s[:,k,0]-s[:,j,0],0)/s[:,0,0,None]/elapsed
# Ten-second trailing window (shorter during startup); no predicted values used.
def group(x):return np.array([x[c==v].mean(0) for v in np.unique(c)])
rows=[]
for threshold in [5e-5,1e-4,2e-4]:
 releasing=fuel>=threshold;drying=(water>=threshold)&~releasing;quiet=(fuel<1e-5)&(water<1e-5);residual=~(releasing|drying|quiet);active=releasing|drying
 row={'fraction_per_second':threshold,'release_active_percent':float(100*group(releasing.mean(1)).mean()),'drying_only_percent':float(100*group(drying.mean(1)).mean()),'weak_residual_percent':float(100*group(residual.mean(1)).mean()),'quiet_percent':float(100*group(quiet.mean(1)).mean()),'active_gas_amount_capture_percent':float(100*group((gas*active).sum(1)).mean()/group(gas.sum(1)).mean()),'quiet_gas_amount_share_percent':float(100*group((gas*quiet).sum(1)).mean()/group(gas.sum(1)).mean())}
 rows.append(row)
 if threshold==1e-4:labels=np.select([releasing,drying,quiet],[1,2,0],default=3).astype('uint8')
out=R/'data/activity_audit';out.mkdir(exist_ok=True);np.savez_compressed(out/'labels.npz',labels=labels,time=t[:,1:],fuel_fraction_rate=fuel,water_fraction_rate=water)
report=dict(definition='Trailing nominal10seconds; active >=0.1% initial relevant mass per10s, quiet both <0.01% per10s; intermediate residual separate. Shorter startup window uses same rate.',fuel='Positive vegetation fuel-gas integral /0.75yield / initialdryfuel /elapsedseconds; inferred pyrolysis-equivalent, NOT combustion/heat.',water='Positive net derivedwater loss /initialwater /elapsedseconds; sensitivity to derived labels retained.',label_codes={'0':'quiet','1':'fuel-release active','2':'drying only','3':'weak residual'},threshold_basis='Declared engineering tolerance, not physical extinction threshold or statistically optimal threshold. Chosen without predictions. All520 histories inspected; descriptive posthoc evaluation, no pristine holdout claim.',weighting='Equal physical configurations; replicas averaged first.',sensitivity=rows,forecast_scope='For16s forecasts report endpoint label AND transitions across the interval separately. Saved aggregate active metrics cannot be relabelled; new inference or retained per-origin predictions are required for new error tables. No errors recomputed here.',limitations='Does not detect gas combustion, char oxidation, or thermal cooling alone. Source-on <=20s is separate metadata, not an activity definition. No external physical validation.')
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows,indent=2))
