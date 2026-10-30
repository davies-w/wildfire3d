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
 proof=json.loads((R/'results/training06-collected.json').read_text());assert proof['passed'] and proof['test_histories']==208
 root=R/'data/training06-results';p=root/'fold00-test-predictions.npz';v=np.load(p);a=np.load(R/'data/training06/data/sequences.npz');ids=v['case_indices']
 expected=json.loads((R/'data/training06/schema.json').read_text())['rotations'][0]['test'];assert ids.tolist()==expected
 assert np.array_equal(v['times'],a['time'][ids])
 pred=np.sinh(v['normalized_rollout']*v['std']+v['mean'])*v['physical_scales'];assert pred.shape==(208,90,4) and np.isfinite(pred).all()
 records=[]
 for j,i in enumerate(ids):
  t=a['time'][i].astype(np.float64);truth=a['state'][i].astype(np.float64);curve=np.concatenate([truth[:1],pred[j].astype(np.float64)],axis=0);span=np.ptp(truth,axis=0);assert np.all(span>0)
  integral=area(t,curve-truth);percent=100*integral/((t[-1]-t[0])*span)
  records.append(dict(id=int(i),configuration=int(a['configuration'][i]),time=t.tolist(),truth=truth.tolist(),prediction=curve.tolist(),simulation_range=span.tolist(),absolute_error_integral=integral.tolist(),percent=percent.tolist()))
 def grouped(key):
  values=np.array([r[key] for r in records]);config=np.array([r['configuration'] for r in records]);return np.stack([values[config==c].mean(0) for c in np.unique(config)]).mean(0)
 result=dict(model='Integral-objective stride-one gated GRU · split3',histories=208,configurations=len(set(r['configuration'] for r in records)),features=['Water kg','Dry fuel kg','Gas kg/s','Heating index K'],aggregate_percent=grouped('percent').tolist(),formula='100 * exact integral(abs(piecewise-linear prediction - simulation)) / (duration * simulation max-minus-min range)',aggregation='Mean replicas within configuration, then equal configurations',scope='Full sequence from initial state; Frozen rotation3, 208 test histories and 204 configurations; same recipe and seed as rotation0. Different test population: not a matched comparison with prior rotation0 models, and not an independent-seed repeat. Previously examined dataset.',forecast_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),records=records)
 out=R/'data/analysis06';out.mkdir(exist_ok=True);(out/'integral-comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:result[k] for k in ['aggregate_percent','histories','configurations']}))
if __name__=='__main__':main()
