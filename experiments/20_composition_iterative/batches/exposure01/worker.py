"""One bounded batch. All cases/parameters fixed before this batch launches."""
import csv,json,tarfile,time
from pathlib import Path
import runner
from scene import ROOT,write
def main():
    spec=json.loads((ROOT/'batch.json').read_text());started=time.monotonic();results=[];error=None
    runner.DATA.mkdir(exist_ok=True);Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
    try:
        for case in spec['cases']:
            remaining=spec['worker_seconds']-(time.monotonic()-started)
            if remaining<720:raise RuntimeError('Budget stop: insufficient time for another complete run')
            c=write(case);r=runner.run(c,min(900,remaining-180));results.append(r)
            if not r['full_horizon']:raise RuntimeError('Incomplete simulation: '+r['case'])
            with (runner.DATA/r['case']/(r['case']+'_devc.csv')).open() as f:
                it=csv.reader(f);next(it);keys=[v.strip().strip('"') for v in next(it)]
                rows=[dict(zip(keys,map(float,v))) for v in it if v]
            hit=next((v['Time'] for v in rows if v['house_burn_max']>1e-9),None)
            r.update(ignited=hit is not None,first_ignition_s=hit,peak_house_C=max(v['house_max'] for v in rows))
    except Exception as exc:error=repr(exc)
    finally:
        runner.save(runner.DATA/'campaign.json',dict(status='complete' if error is None else 'incomplete',error=error,results=results,wall_s=time.monotonic()-started))
        with tarfile.open('/tmp/summary.tar.gz','w:gz') as t:
            t.add(runner.DATA/'campaign.json',arcname='campaign.json');t.add(ROOT/'decks',arcname='generated-decks')
        runner.upload(Path('/tmp/summary.tar.gz'),'summary.tar.gz')
        print(json.dumps(dict(status='complete' if error is None else 'incomplete',completed=len(results),error=error)),flush=True)
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
