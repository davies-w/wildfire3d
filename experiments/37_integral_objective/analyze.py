"""Whole-sequence physical integral comparison; requires verified terminal collection."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parent

def area(t,d):
 a=np.abs(d[:-1]);b=np.abs(d[1:]);cross=d[:-1]*d[1:]<0
 avg=(a+b)/2;np.divide(a*a+b*b,2*(a+b),out=avg,where=cross)
 return (np.diff(t)[:,None]*avg).sum(0)

def main():
 proof=json.loads((R/'results/training03-collected.json').read_text());assert proof['passed'] and proof['test_histories']==208
 root=R/'data/training03-results';p=root/'fold00-test-predictions.npz';v=np.load(p);a=np.load(R/'data/training03/data/sequences.npz');ids=v['case_indices']
 expected=json.loads((R/'data/training03/schema.json').read_text())['rotations'][0]['test'];assert ids.tolist()==expected
 assert np.array_equal(v['times'],a['time'][ids])
 pred=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales'];assert pred.shape==(208,90,4) and np.isfinite(pred).all()
 old=json.loads((R.parent/'36_tree_density/data/stride-integral/integral-scores.json').read_text());prior={r['id']:r for r in old['records']};assert set(prior)==set(ids.tolist())
 records=[]
 for j,i in enumerate(ids):
  t=a['time'][i].astype(np.float64);truth=a['state'][i].astype(np.float64);curve=np.concatenate([truth[:1],pred[j].astype(np.float64)],axis=0);span=np.ptp(truth,axis=0);assert np.all(span>0)
  integral=area(t,curve-truth);percent=100*integral/((t[-1]-t[0])*span)
  records.append(dict(id=int(i),configuration=int(a['configuration'][i]),time=t.tolist(),truth=truth.tolist(),prediction=curve.tolist(),simulation_range=span.tolist(),absolute_error_integral=integral.tolist(),percent=percent.tolist(),prior_percent=prior[int(i)]['percent']))
 def grouped(key):
  values=np.array([r[key] for r in records]);config=np.array([r['configuration'] for r in records]);return np.stack([values[config==c].mean(0) for c in np.unique(config)]).mean(0)
 oldmean=grouped('prior_percent');assert np.allclose(oldmean,old['aggregate_percent'],rtol=1e-12,atol=1e-12)
 result=dict(model='Integral-objective stride-one gated GRU · split0',histories=208,configurations=len(set(r['configuration'] for r in records)),features=['Water kg','Dry fuel kg','Gas kg/s','Heating index K'],aggregate_percent=grouped('percent').tolist(),prior_aggregate_percent=oldmean.tolist(),difference_percentage_points=(grouped('percent')-oldmean).tolist(),formula='100 * exact integral(abs(piecewise-linear prediction - simulation)) / (duration * simulation max-minus-min range)',aggregation='Mean replicas within configuration, then equal configurations',scope='Full sequence from initial state; same208 test histories. Previously examined test population; exploratory matched comparison, not pristine confirmation. Objective, selection metric and active/quiet weighting changed together.',forecast_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),records=records)
 out=R/'data/analysis';out.mkdir(exist_ok=True);(out/'integral-comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['aggregate_percent','prior_aggregate_percent','difference_percentage_points']}))
if __name__=='__main__':main()
