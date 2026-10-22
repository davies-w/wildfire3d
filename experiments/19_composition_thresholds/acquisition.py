"""Bounded, model-independent acquisition policy; no cloud API or solver invocation.

An execution adapter must supply solve(request) returning a completed FDS
record with a boolean ignition label. This policy can be tested without FDS.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

class CoverageError(RuntimeError):
    pass

def acquire(solve):
    d=json.loads((ROOT/'design.json').read_text());new=[]
    def run(layout,power,role,seed=1234):
        if len(new)>=d['max_new_runs']:raise CoverageError('New-case allowance exhausted')
        assert 0<power<=d['max_source_kw']
        request=dict(case=f'{role}_{len(new)+1:02d}_{layout}_s{seed}',layout=layout,
                     total_source_kw=float(power),split=role,seed=seed,horizon_s=90)
        result=solve(request)
        if result.get('full_horizon') is not True or type(result.get('ignited')) is not bool:
            raise CoverageError('Incomplete case cannot be classified: '+request['case'])
        record=dict(request,ignited=result['ignited']);new.append(record)
        return record
    def known(layout,role):
        return [dict(r,ignited=r['old_ignited']) for r in d['reuse'] if r['layout']==layout and r['role']==role]
    def bracket(layout,low,ladder,role):
        if low['ignited']:raise CoverageError('Starting low endpoint ignites: '+layout)
        high=None
        for power in ladder:
            candidate=run(layout,power,role)
            if candidate['ignited']:
                high=candidate;break
            low=candidate
        if high is None:raise CoverageError('No positive endpoint inside the supported range: '+layout)
        return low,high

    for r in d['training_additions']:run(r['layout'],r['total_source_kw'],'train')
    # Reuse all three AC negatives; replace the all-negative BD validation layout
    # with AD, whose nearest-wall component is represented in training.
    ac=known('AC','validation')
    if not ac or any(r['ignited'] for r in ac):raise CoverageError('AC reuse evidence differs from preregistration')
    bracket('AC',max(ac,key=lambda r:r['total_source_kw']),d['validation_high_ladder_kw'],'validation')
    ad_low=run('AD',d['validation_AD_low_kw'],'validation')
    bracket('AD',ad_low,d['validation_high_ladder_kw'],'validation')
    for layout in d['validation_layouts']:
        records=known(layout,'validation')+[r for r in new if r['split']=='validation' and r['layout']==layout]
        if {r['ignited'] for r in records}!={False,True}:raise CoverageError('Validation missing a class: '+layout)

    thresholds={};confirmation_inputs=[]
    for layout in d['test_layouts']:
        reused=known(layout,'bracket_only')
        assert len(reused)==1
        low,high=bracket(layout,reused[0],d['test_high_ladder_kw'],'bracket_only')
        for _ in range(d['test_midpoint_runs_per_layout']):
            midpoint=run(layout,(low['total_source_kw']+high['total_source_kw'])/2,'bracket_only')
            if midpoint['ignited']:high=midpoint
            else:low=midpoint
        thresholds[layout]=dict(low_kw=low['total_source_kw'],high_kw=high['total_source_kw'],
            relative_width=(high['total_source_kw']-low['total_source_kw'])/high['total_source_kw'])
        # Margin makes confirmation more robust to the changed FDS random seed.
        low_power=d['low_margin_factor']*low['total_source_kw']
        high_power=min(d['max_source_kw'],d['high_margin_factor']*high['total_source_kw'])
        for seed in d['confirmation_seeds']:
            for power in (low_power,high_power):
                confirmation_inputs.append(dict(layout=layout,total_source_kw=power,seed=seed))
    # All brackets must be established before spending on confirmation runs.
    confirmations=[run(r['layout'],r['total_source_kw'],'test',r['seed']) for r in confirmation_inputs]
    for layout in d['test_layouts']:
        if {r['ignited'] for r in confirmations if r['layout']==layout}!={False,True}:
            raise CoverageError('Final confirmation lacks both classes: '+layout)
    positives=sum(r['ignited'] for r in confirmations)
    if not 4<=positives<=8:raise CoverageError('Final test class balance outside 4–8 positive cases')
    return dict(status='coverage_passed',new_runs=new,thresholds=thresholds,
                confirmation_inputs=confirmation_inputs,positive_confirmations=positives)

def selftest():
    """Exercise success, worst-case acquisition and mandatory early-stop gates."""
    reports=[]
    def simulator(thresholds,force_confirmation=None):
        def solve(r):
            label=r['total_source_kw']>=thresholds.get(r['layout'],1000)
            if r['split']=='test' and force_confirmation is not None:label=force_confirmation
            return dict(full_horizon=True,ignited=bool(label))
        return solve
    easy=acquire(simulator(dict(AC=1500,AD=1500,ABC=1700,ABD=2000,ACD=2200)))
    assert easy['positive_confirmations']==6
    reports.append(dict(check='balanced_confirmation',passed=True,new_runs=len(easy['new_runs'])))
    worst=acquire(simulator({k:3000 for k in ['AC','AD','ABC','ABD','ACD']}))
    assert len(worst['new_runs'])==37
    reports.append(dict(check='worst_case_run_ceiling',passed=True,new_runs=37))
    for name,solver in [
        ('unreachable_positive',simulator(dict(AC=4000))),
        ('unexpected_low_ignition',simulator(dict(AC=1500,AD=500))),
        ('unbalanced_confirmations',simulator(dict(AC=1500,AD=1500,ABC=1700,ABD=2000,ACD=2200),False)),
        ('incomplete_run',lambda r:dict(full_horizon=False,ignited=False))]:
        try:acquire(solver)
        except CoverageError:reports.append(dict(check=name,passed=True))
        else:raise AssertionError(name+' did not stop')
    (ROOT/'results/acquisition-check.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports,indent=2))
if __name__=='__main__':selftest()
