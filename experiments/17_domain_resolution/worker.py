"""One bounded adaptive campaign. Incomplete runs never count as non-ignitions."""
import json,time,tarfile,platform,csv
from pathlib import Path
import runner
from generate import write,HORIZON,ROOT

def outcome(r):
    p=runner.DATA/r['case']/(r['case']+'_devc.csv')
    with p.open() as f:
        rows=csv.reader(f);next(rows);keys=[s.strip().strip('"') for s in next(rows)]
        vals=[dict(zip(keys,map(float,v))) for v in rows if v]
    hit=next((v['Time'] for v in vals if v['house_max']>=350.),None)
    return dict(ignited=hit is not None if r['full_horizon'] else None,first_ignition_s=hit,peak_house_C=max(v['house_max'] for v in vals),initial_fuel_mass_kg={k:vals[0][k] for k in keys if k.startswith('mass ')})

def main():
    runner.DATA.mkdir(exist_ok=True);Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
    start=time.monotonic();results=[];serial=0
    def case(mode,power,phase,seed=1234):
        nonlocal serial
        remaining=9900-(time.monotonic()-start)
        if remaining<180:raise RuntimeError('Campaign time allowance exhausted')
        serial+=1;c=write(f'{phase}_{serial:02d}_{mode}',mode,power,seed=seed)
        c['phase']=phase;r=runner.run(c,min(1200,remaining-120));r.update(outcome(r));results.append(r)
        # runner archive contains measurements; summary adds derived threshold classification.
        if r['returncode'] or not r['full_horizon']:raise RuntimeError('Incomplete case; cannot classify ignition: '+r['case'])
        return r
    status='complete';error=None;bracket=None
    try:
        # Fixed-duration pilot ignition under both particle crowns. Parameter is source strength,
        # NOT a manufactured change to the structure ignition threshold.
        lo=case('full',100.,'calibrate');hi=case('full',2400.,'calibrate')
        if lo['ignited']:lo=case('full',0.,'calibrate')
        if not hi['ignited']:hi=case('full',4800.,'calibrate')
        if lo['ignited'] or not hi['ignited']:raise RuntimeError('No ignition bracket found; do not claim near-threshold coverage')
        for _ in range(5):
            if hi['power_kw_m2']-lo['power_kw_m2'] <= .1*hi['power_kw_m2']:break
            mid=case('full',(lo['power_kw_m2']+hi['power_kw_m2'])/2,'calibrate')
            if mid['ignited']:hi=mid
            else:lo=mid
        bracket=dict(nonigniting=lo,igniting=hi,relative_width=(hi['power_kw_m2']-lo['power_kw_m2'])/hi['power_kw_m2'])
        # Execute paired comparisons first; preserve evidence if later budget termination occurs.
        for mode in ['mixed','tight','combined','wide']:
            for ref in [lo,hi]:case(mode,ref['power_kw_m2'],'compare')
        # An independent particle/turbulence seed tests whether the bracket is robust.
        for ref in [lo,hi]:case('full',ref['power_kw_m2'],'seedcheck',4321)
    except Exception as e:status='incomplete';error=repr(e)
    finally:
        summary=dict(status=status,error=error,bracket=bracket,results=results,total_wall_s=time.monotonic()-start,horizon_s=HORIZON,platform=platform.platform(),cpuinfo=Path('/proc/cpuinfo').read_text(),source_revision='ff928dbf68a2623ced3a007be75391c6dc6c9f90')
        runner.save(runner.DATA/'campaign.json',summary)
        with tarfile.open('/tmp/summary.tar.gz','w:gz') as t:
            t.add(runner.DATA/'campaign.json',arcname='campaign.json')
            t.add(ROOT/'decks',arcname='generated-decks')
        runner.upload(Path('/tmp/summary.tar.gz'),'summary.tar.gz')
        print(json.dumps(summary),flush=True)
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
