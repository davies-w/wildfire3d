"""Synthetic integration check; no scientific results and no cloud calls."""
import contextlib,io,json,shutil,tempfile
from pathlib import Path
import models,train,predict,evaluate
ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='composition19-check-') as temporary:
    p=Path(temporary)
    for d in ('results','data/cloud'):(p/d).mkdir(parents=True)
    for n in ('design.json','models.py','train.py'):shutil.copy2(ROOT/n,p/n)
    cfg=json.loads((ROOT/'training.json').read_text());cfg.update(epochs=20,seeds=[11])
    (p/'training.json').write_text(json.dumps(cfg))
    for module in (models,train,predict,evaluate):module.ROOT=p
    dev=[]
    for split,layouts,powers in [('train',['A','B','C','D','AB','CD'],[200,500,800,1200,1800,3200]),
                                 ('validation',['AC','AD'],[800,1600,2400])]:
        for layout in layouts:
            for power in powers:
                dev.append(dict(case=f'{split}_{layout}_{power}',layout=layout,split=split,
                    total_source_kw=power,target=[int(power>=1500),.5 if power>=1500 else 1.],auxiliary=[[0.]*12 for _ in range(5)]))
    (p/'data/development.json').write_text(json.dumps(dev))
    with contextlib.redirect_stdout(io.StringIO()):train.train()
    assert (p/'results/frozen-weights.json').exists()
    assert not (p/'data/cloud/confirmation-inputs.json').exists()
    inputs=[dict(case=f'test_{layout}_{power}_{seed}',layout=layout,total_source_kw=power,seed=seed)
            for layout in ('ABC','ABD','ACD') for seed in (4321,5678) for power in (1200,2400)]
    (p/'data/cloud/confirmation-inputs.json').write_text(json.dumps(inputs))
    with contextlib.redirect_stdout(io.StringIO()):predict.main()
    assert (p/'results/frozen-predictions.json').exists()
    assert not (p/'data/test.json').exists()
    tests=[dict(r,target=[int(r['total_source_kw']>1500),.5],auxiliary=[[0.]*12 for _ in range(5)]) for r in inputs]
    (p/'data/test.json').write_text(json.dumps(tests))
    with contextlib.redirect_stdout(io.StringIO()):evaluate.main()
    report=json.loads((p/'results/evaluation.json').read_text())
    assert all(report['coverage_by_layout'].values()) and report['positive_test_cases']==6
    for r in tests:r['target'][0]=0
    (p/'data/test.json').write_text(json.dumps(tests))
    with contextlib.redirect_stdout(io.StringIO()):evaluate.main()
    assert json.loads((p/'results/evaluation.json').read_text())['verdict']=='inconclusive_coverage_gate_failed'
(ROOT/'results/pipeline-check.json').write_text(json.dumps(dict(passed=True,synthetic_only=True,
    fit_without_confirmation_inputs=True,predict_without_confirmation_outputs=True,
    all_negative_score_rejected=True),indent=2)+'\n')
print('Synthetic fit/freeze/predict/score ordering and all-negative rejection passed.')
