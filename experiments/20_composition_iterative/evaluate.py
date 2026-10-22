"""Evaluate frozen predictions; never fit or tune on confirmation outcomes."""
import hashlib,json
import numpy as np
from models import ROOT

def metrics(y,p):
    pos=y==1;neg=y==0;pred=p>=.5
    return dict(n=len(y),positives=int(pos.sum()),negatives=int(neg.sum()),brier=float(np.mean((p-y)**2)),
        accuracy=float(np.mean(pred==y)),positive_recall=float(pred[pos].mean()) if pos.any() else None,
        negative_recall=float((~pred[neg]).mean()) if neg.any() else None,
        balanced_accuracy=float((pred[pos].mean()+(~pred[neg]).mean())/2) if pos.any() and neg.any() else None)
def main():
    frozen=json.loads((ROOT/'results/frozen-predictions.json').read_text())
    assert hashlib.sha256((ROOT/'confirmation-inputs.json').read_bytes()).hexdigest()==frozen['confirmation_inputs_sha256']
    assert hashlib.sha256((ROOT/'results/frozen-weights.json').read_bytes()).hexdigest()==frozen['frozen_weights_sha256']
    tests=json.loads((ROOT/'data/test.json').read_text());labels={r['case']:r['target'][0] for r in tests};names=list(labels);y=np.array([labels[n] for n in names]);results={}
    for kind in ('graph','additive','simple','ignition_only'):
        runs=[];all_p=[]
        for row in frozen['models']:
            if row['kind']!=kind:continue
            lookup={r['case']:r['ignition_probability'] for r in row['predictions']};assert set(lookup)==set(labels)
            p=np.array([lookup[n] for n in names]);all_p.append(p);runs.append(dict(seed=row['seed'],metrics=metrics(y,p),inference_s=row['inference_seconds_per_case']))
        p=np.mean(all_p,axis=0);results[kind]=dict(seeds=runs,ensemble=metrics(y,p),predictions=dict(zip(names,p.tolist())),
            per_layout={layout:metrics(y[mask],p[mask]) for layout in sorted({r['layout'] for r in tests}) for mask in [np.array([r['layout']==layout for r in tests])]})
    development=json.loads((ROOT/'data/development.json').read_text());prior=np.mean([r['target'][0] for r in development if r['split']=='train'])
    groups={}
    for r in tests:
        key=(r['layout'],r['total_source_kw'],r.get('duration_s',20))
        groups.setdefault(key,[]).append(r)
    repeated=[dict(layout=k[0],total_source_kw=k[1],duration_s=k[2],runs=len(v),
        ignitions=sum(r['target'][0] for r in v),seed_disagreement=len({r['target'][0] for r in v})>1,
        cases=[r['case'] for r in v]) for k,v in groups.items()]
    report=dict(repeated_conditions=repeated,unique_initial_conditions=len(groups),
        conditions_with_seed_disagreement=sum(r['seed_disagreement'] for r in repeated),
        coverage=metrics(y,np.zeros(len(y))),models=results,baselines={str(p):metrics(y,np.full(len(y),p)) for p in (0.,1.,.5,float(prior))},
        caution='Small synthetic, fixed-house/fixed-weather test. Optimization seed spread is not uncertainty about real wildfire risk. Two FDS seeds per condition do not establish a reliable ignition probability; repeated runs are not independent geometry coverage. No field validation.',
        conclusions='INCONCLUSIVE: test has only one class' if len(set(y))<2 else 'Both classes present. Compare held-out Brier and class recalls; this small sample cannot prove general composition.')
    (ROOT/'results/evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['conclusions'])
    for k,v in results.items():print(k,v['ensemble'])
if __name__=='__main__':main()
