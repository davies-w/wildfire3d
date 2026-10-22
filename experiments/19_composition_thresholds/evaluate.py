"""Coverage-gated confirmation scoring of already frozen models."""
import hashlib,json
import numpy as np
from models import ROOT
def main():
    tests=json.loads((ROOT/'data/test.json').read_text());assert len(tests)==12
    lookup={r['case']:r for r in tests};layouts=('ABC','ABD','ACD')
    coverage={l:{r['target'][0] for r in tests if r['layout']==l}=={0,1} for l in layouts}
    positives=sum(r['target'][0] for r in tests)
    gated=all(coverage.values()) and 4<=positives<=8
    frozen=ROOT/'results/frozen-predictions.json';predictions=json.loads(frozen.read_text())
    summaries=[]
    for m in predictions['models']:
        records=[lookup[r['case']] for r in m['predictions']]
        y=np.array([r['target'][0] for r in records]);p=np.array([r['ignition_probability'] for r in m['predictions']])
        accuracy=[]
        for l in layouts:
            for label in (0,1):
                mask=np.array([r['layout']==l and r['target'][0]==label for r in records])
                if mask.any():accuracy.append(float(((p[mask]>=.5)==y[mask]).mean()))
        aux=np.array([r['auxiliary'] for r in m['predictions']]);truth=np.array([r['auxiliary'] for r in records])
        summaries.append(dict(kind=m['kind'],seed=m['seed'],correct=int(((p>=.5)==y).sum()),
            false_negatives=int(((p<.5)&(y==1)).sum()),false_positives=int(((p>=.5)&(y==0)).sum()),
            balanced_accuracy=float(np.mean(accuracy)),brier=float(np.mean((p-y)**2)),
            face_temperature_mae_C=float(np.mean(abs(aux[:,:,:6]-truth[:,:,:6]))*350),
            inference_seconds_per_case=m['inference_seconds_per_case']))
    groups={k:[r for r in summaries if r['kind']==k] for k in ('graph','additive','simple')}
    means={k:float(np.mean([r['brier'] for r in rows])) for k,rows in groups.items()}
    wins=0
    for g in groups['graph']:
        bases=[next(r for r in groups[k] if r['seed']==g['seed']) for k in ('additive','simple')]
        wins+=int(g['correct']>=10 and g['false_negatives']<=1 and all(g['brier']<=.8*b['brier'] for b in bases))
    verdict='promising_composition_signal' if gated and wins>=4 else 'no_composition_advantage_demonstrated'
    if not gated:verdict='inconclusive_coverage_gate_failed'
    result=dict(verdict=verdict,coverage_by_layout=coverage,positive_test_cases=positives,
        qualifying_graph_seeds=wins,mean_brier=means,models=summaries,
        always_negative=dict(correct=12-positives,false_negatives=positives,brier=positives/12,balanced_accuracy=.5 if gated else None),
        frozen_predictions_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),
        limitation='Three layouts, two FDS seeds each, deliberately selected exposure brackets. Not twelve independent properties or population probability calibration.')
    (ROOT/'results/evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
    text=f"# Confirmation findings\n\nVerdict: {verdict}.\n\nIgniting confirmation cases: {positives}/12. Coverage by layout: {coverage}.\n\n"
    text+='| Model | Mean Brier |\n|---|---:|\n'+''.join(f'| {k} | {v:.5f} |\n' for k,v in means.items())
    text+='\n'+result['limitation']+'\n\nLabels cross-checked using fds2ascii over all six structure faces, burning rate averaged over 0–90 s (>1e-12 kg/m²/s), against instantaneous device burning rate (>1e-9 kg/m²/s).\n'
    (ROOT/'results/findings.md').write_text(text)
    print(json.dumps({k:result[k] for k in ('verdict','positive_test_cases','coverage_by_layout','mean_brier')},indent=2))
if __name__=='__main__':main()
