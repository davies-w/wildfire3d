"""Partial scalar diagnostics only; strict final comparison remains compare.py."""
import json
from compare import R,OLD,csv_rows,scalar_compare
cases=json.loads((R/'data/cases.json').read_text());originals={}
for group in ['canaries04','completed05','completed06','completed07']:
 for p in (OLD/'data'/group).glob('*/solve'):originals[p.parent.name]=p
proof=json.loads((R/'data/completed/proof.json').read_text());assert proof['passed'];rows=[]
for p in proof['cases']:
 assert p['passed'] and p['physical_time_s']>=180-1e-5
 c=next(x for x in cases if x['pilot_case']==p['case']);on=c['original_case'];nn=c['pilot_case'];o=originals[on];n=R/'data/completed'/nn/'solve'
 m=scalar_compare(csv_rows(o/(on+'_hrr.csv')),csv_rows(n/(nn+'_hrr.csv')),csv_rows(o/(on+'_devc.csv')),csv_rows(n/(nn+'_devc.csv')),sum(c['expected_wet_mass_kg'].values()));rows.append(dict(case=nn,metrics=m))
(R/'private/partial-canary-scalar-comparison.json').write_text(json.dumps(dict(complete=False,temperature_comparison_pending=True,cases=rows),indent=2)+'\n');print('Partial scalar checks:',len(rows),'cases; temperature/equivalence conclusion pending')
