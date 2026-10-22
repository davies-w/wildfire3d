"""One bounded campaign; test outcomes are retained but never printed or used adaptively."""
import csv
import json
import platform
import tarfile
import time
from pathlib import Path
import runner
from generate import ROOT, HORIZON, write

def outcome(r):
    with (runner.DATA/r['case']/(r['case']+'_devc.csv')).open() as f:
        it=csv.reader(f); next(it)
        keys=[s.strip().strip('"') for s in next(it)]
        rows=[dict(zip(keys,map(float,v))) for v in it if v]
    hit=next((v['Time'] for v in rows if v['house_burn_max']>1e-9),None)
    return dict(ignited=hit is not None if r['full_horizon'] else None,
                first_ignition_s=hit,peak_house_C=max(v['house_max'] for v in rows))

def main():
    runner.DATA.mkdir(exist_ok=True)
    Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
    design=json.loads((ROOT/'design.json').read_text())
    started=time.monotonic(); results=[]; bracket=None; p0=None
    def run(name,layout,power,split):
        remaining=17100-(time.monotonic()-started)
        if remaining<720:
            raise RuntimeError('Campaign deadline: insufficient allowance for another complete case')
        c=write(name,layout,power,split=split)
        r=runner.run(c,min(900,remaining-180))
        if not r['full_horizon'] or r['returncode']:
            results.append(r)
            raise RuntimeError('Incomplete case '+name+'; never classify as non-ignition')
        r.update(outcome(r)); results.append(r)
        return r
    status='complete'; error=None
    try:
        lo=run('calibration_01','AB',200.,'calibration')
        hi=run('calibration_02','AB',3200.,'calibration')
        if lo['ignited'] or not hi['ignited']:
            raise RuntimeError('Calibration endpoints do not bracket ignition; stop without expanding budget')
        for i in range(4):
            mid=run(f'calibration_{i+3:02d}','AB',(lo['total_source_kw']+hi['total_source_kw'])/2,'calibration')
            if mid['ignited']: hi=mid
            else: lo=mid
        bracket={'low_kw':lo['total_source_kw'],'high_kw':hi['total_source_kw'],
                 'relative_width':(hi['total_source_kw']-lo['total_source_kw'])/hi['total_source_kw']}
        p0=(lo['total_source_kw']+hi['total_source_kw'])/2
        runner.save(runner.DATA/'calibration.json',dict(bracket=bracket,p0_kw=p0))
        # Publish calibration only so local feature generation can proceed without test labels.
        with tarfile.open('/tmp/calibration.tar.gz','w:gz') as t:
            t.add(runner.DATA/'calibration.json',arcname='calibration.json')
        runner.upload(Path('/tmp/calibration.tar.gz'),'calibration.tar.gz')
        for row in design['cases']:
            run(row['case'].replace('.','p'),row['layout'],p0*row['total_source_power_factor'],row['split'])
    except Exception as e:
        status='incomplete'; error=repr(e)
    finally:
        summary=dict(status=status,error=error,bracket=bracket,p0_kw=p0,results=results,
                     total_wall_s=time.monotonic()-started,horizon_s=HORIZON,
                     platform=platform.platform(),source_revision='ff928dbf68a2623ced3a007be75391c6dc6c9f90')
        runner.save(runner.DATA/'campaign.json',summary)
        with tarfile.open('/tmp/summary.tar.gz','w:gz') as t:
            t.add(runner.DATA/'campaign.json',arcname='campaign.json')
            t.add(ROOT/'decks',arcname='generated-decks')
        runner.upload(Path('/tmp/summary.tar.gz'),'summary.tar.gz')
        print(json.dumps(dict(status=status,error=error,completed=len(results),bracket=bracket)),flush=True)
    if error: raise RuntimeError(error)

if __name__=='__main__': main()
