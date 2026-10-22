"""Single bounded FDS acquisition job. No model fitting or automatic retries."""
import csv,json,tarfile,time
from pathlib import Path
import runner
from generate import ROOT,write
from acquisition import acquire

def main():
    runner.DATA.mkdir(exist_ok=True)
    Path('/fds/Build/ompi_gnu_linux').mkdir(parents=True,exist_ok=True)
    started=time.monotonic();results=[];policy=None;error=None
    def solve(request):
        remaining=17100-(time.monotonic()-started)
        if remaining<720:raise RuntimeError('Insufficient campaign time for another full run')
        c=write(request['case'],request['layout'],request['total_source_kw'],seed=request['seed'],split=request['split'])
        r=runner.run(c,min(900,remaining-180));results.append(r)
        if not r['full_horizon']:return dict(full_horizon=False,ignited=None)
        with (runner.DATA/r['case']/(r['case']+'_devc.csv')).open() as f:
            rows=csv.reader(f);next(rows);keys=[v.strip().strip('"') for v in next(rows)]
            vals=[dict(zip(keys,map(float,v))) for v in rows if v]
        hit=next((v['Time'] for v in vals if v['house_burn_max']>1e-9),None)
        r.update(ignited=hit is not None,first_ignition_s=hit)
        return r
    try:policy=acquire(solve)
    except Exception as exc:error=repr(exc)
    finally:
        status='complete' if error is None else 'needs_attention'
        runner.save(runner.DATA/'completion-status.json',dict(status=status,error=error,completed=len(results)))
        runner.save(runner.DATA/'campaign.json',dict(status=status,error=error,policy=policy,
            results=results,total_wall_s=time.monotonic()-started))
        # Separate input-only manifests avoid exposing confirmation metadata to fitting.
        public=lambda r:{k:r[k] for k in ('case','layout','total_source_kw','split','seed','horizon_s')}
        runner.save(runner.DATA/'development-manifest.json',[public(r) for r in results if r['split'] in ('train','validation')])
        runner.save(runner.DATA/'confirmation-inputs.json',[public(r) for r in results if r['split']=='test'])
        with tarfile.open('/tmp/summary.tar.gz','w:gz') as t:
            for n in ('campaign.json','completion-status.json','development-manifest.json','confirmation-inputs.json'):t.add(runner.DATA/n,arcname=n)
            t.add(ROOT/'decks',arcname='generated-decks')
        runner.upload(Path('/tmp/summary.tar.gz'),'summary.tar.gz')
        print(json.dumps(dict(status=status,completed=len(results),error=error)),flush=True)
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
