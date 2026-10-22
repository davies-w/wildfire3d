"""Score once-frozen predictions; never select or refit a model using test evidence."""
import hashlib
import json
import numpy as np
from models import ROOT
def main():
    predictions=json.loads((ROOT/'results/frozen-predictions.json').read_text())
    tests=json.loads((ROOT/'data/test.json').read_text());lookup={r['case']:r for r in tests}
    assert len(tests)==12
    summaries=[]
    for m in predictions['models']:
        probabilities=np.array([r['ignition_probability'] for r in m['predictions']])
        y=np.array([lookup[r['case']]['target'][0] for r in m['predictions']])
        au=np.array([r['auxiliary'] for r in m['predictions']]);truth=np.array([lookup[r['case']]['auxiliary'] for r in m['predictions']])
        summaries.append(dict(kind=m['kind'],seed=m['seed'],correct=int(((probabilities>=.5)==y).sum()),
            false_negatives=int(((probabilities<.5)&(y==1)).sum()),brier=float(np.mean((probabilities-y)**2)),
            face_temperature_mae_C=float(np.mean(abs(au[:,:,:6]-truth[:,:,:6]))*350),
            inference_seconds_per_case=m['inference_seconds_per_case']))
    kinds={k:[r for r in summaries if r['kind']==k] for k in ('graph','additive','simple')}
    means={k:float(np.mean([r['brier'] for r in rs])) for k,rs in kinds.items()}
    wins=0
    for g in kinds['graph']:
        bases=[next(r for r in kinds[k] if r['seed']==g['seed']) for k in ('additive','simple')]
        wins+=int(g['correct']>=10 and g['false_negatives']<=1 and all(g['brier']<=.8*b['brier'] for b in bases))
    coverage={r['target'][0] for r in tests}=={0,1}
    trivial=any(np.mean([r['correct'] for r in kinds[k]])>=11.5 for k in ('additive','simple'))
    promising=coverage and not trivial and wins>=4 and all(means['graph']<=.8*means[k] for k in ('additive','simple'))
    verdict='promising_composition_signal' if promising else 'no_composition_advantage_demonstrated'
    if not coverage:verdict='inconclusive_test_lacks_both_classes'
    elif trivial:verdict='inconclusive_baseline_already_nearly_perfect'
    result=dict(verdict=verdict,positive_test_cases=sum(r['target'][0] for r in tests),
        qualifying_graph_seeds=wins,mean_brier=means,models=summaries,
        frozen_sha256=hashlib.sha256((ROOT/'results/frozen-predictions.json').read_bytes()).hexdigest(),
        limitation='Four test layouts, one FDS seed, fixed wind/material/moisture; not physical validation or probability calibration.')
    (ROOT/'results/evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
    text=f"# Composition pilot findings\n\nVerdict: {verdict}.\n\nPositive test cases: {result['positive_test_cases']}/12. Qualifying training seeds: {wins}/5.\n\n"
    text+='| Model | Mean Brier score |\n|---|---:|\n'+''.join(f'| {k} | {v:.5f} |\n' for k,v in means.items())
    text+='\n'+result['limitation']+'\n\nRaw six-face burning-rate data was extracted with fds2ascii over 0–90 s and cross-checked against device ignition labels. Numerical thresholds: boundary time average >1e-12 kg/m²/s; instantaneous device >1e-9 kg/m²/s.\n'
    (ROOT/'results/findings.md').write_text(text)
    print(json.dumps({k:result[k] for k in ('verdict','positive_test_cases','qualifying_graph_seeds','mean_brier')},indent=2))
if __name__=='__main__':main()
