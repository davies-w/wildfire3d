"""Report complete and censored Stage A evidence without launching any work."""
import json,datetime
from pathlib import Path
from finish_stage_a import ROOT,audit,compare
cases=[]
for p in sorted((ROOT/'data/cloud').glob('*/result.json')):
 r=json.loads(p.read_text())
 if r['full_horizon']:cases.append(dict(audit(r['case']),complete=True))
 else:cases.append(dict(case=r['case'],complete=False,physical_seconds_reached=r['physical_seconds_reached'],wall_seconds=r['wall_seconds'],stopped_by_budget=r['stopped_by_budget']))
comparisons=[compare(a,b) for a,b in json.loads((ROOT/'comparison-pairs.json').read_text()) if next(r for r in cases if r['case']==b)['complete']]
seconds=0
for p in (ROOT/'jobs').glob('*/status.json'):
 s=json.loads(p.read_text())
 start=datetime.datetime.fromisoformat(s['startTime'].replace('Z','+00:00'));end=datetime.datetime.fromisoformat(s['endTime'].replace('Z','+00:00'));seconds+=(end-start).total_seconds()
report=dict(status='not_passed',reason='No igniting coverage; refinement incomplete; see completed context comparisons.',cases=cases,comparisons=comparisons,cost=dict(controller_vm_hours_upper=seconds/3600,compute_estimate_usd=seconds/3600*.079528,ancillary_allowance_usd=.54,estimate_plus_ancillary_usd=seconds/3600*.079528+.54,reserved_usd=1.5,invoice_verified=False),no_training_started=True)
(ROOT/'results/stage-a.json').write_text(json.dumps(report,indent=2))
for r in comparisons:
 p=r['probes'];print(r['compact'],r['reference'],'pass',r['passed'],'failed probes',sum(not x['passed'] for x in p),'max dose error',max(x['relative_dose_error'] for x in p if x['exposed']),'max temp MAE',max(x['temperature_mae_C'] for x in p))
print([(r['case'],r.get('peak_house_C')) for r in cases]);print(report['cost'])
