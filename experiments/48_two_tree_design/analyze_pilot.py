"""Summarize verified FDS CSV outputs; no solver or neural model execution."""
import argparse,csv,json,lzma,math
from pathlib import Path
R=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args()
payload=json.loads(lzma.decompress((R/'data/cloud05/input.xz').read_bytes()));groups=json.loads(payload['groups.json']);config={c['pilot_case']:c for cs in groups.values() for c in cs}
def read_csv(path):
 with path.open() as f:
  reader=csv.reader(f);next(reader);keys=[s.strip().strip('"') for s in next(reader)];rows=[dict(zip(keys,map(float,row))) for row in reader if row]
 assert all(all(math.isfinite(v) for v in row.values()) for row in rows)
 assert all(b['Time']>=a['Time'] for a,b in zip(rows,rows[1:]))
 return rows
def integral(rows,start):
 total=0.
 for a,b in zip(rows,rows[1:]):
  lo=max(a['Time'],start);hi=b['Time'];dt=hi-a['Time']
  if hi<=lo or dt<=0:continue
  y=a['HRR']+(b['HRR']-a['HRR'])*(lo-a['Time'])/dt;total+=(y+b['HRR'])*(hi-lo)/2
 return total
cases={}
for group in ['canaries04','completed05','completed06','completed07']:
 root=R/'data'/group
 if not (root/'proof.json').exists():continue
 proof=json.loads((root/'proof.json').read_text());assert proof['passed']
 for item in proof['cases']:
  name=item['case'];assert name not in cases and item['passed'] and item['physical_time_s']>=180-1e-5
  c=config[name];folder=root/name/'solve';h=read_csv(folder/(name+'_hrr.csv'));d=read_csv(folder/(name+'_devc.csv'));assert h[-1]['Time']>=180-1e-5 and d[-1]['Time']>=180-1e-5
  initial=sum(c['expected_wet_mass_kg'].values());final=sum(v for k,v in d[-1].items() if k.endswith(' mass'))
  cases[name]=dict(case=name,type_id=c['type_id'],geometry_id=c['geometry_id'],variant=c['variant'],ignition_mode=c['ignition']['mode'],wind_m_s=c['wind_m_s'],moisture_fraction=c['moisture_fraction'],loading_multiplier=c['loading_multiplier'],dx_m=c['dx'],domain_m=c['domain'],end_time_s=d[-1]['Time'],peak_hrr_kw=max(x['HRR'] for x in h),final_hrr_kw=h[-1]['HRR'],energy_kj=integral(h,0),energy_after_20s_kj=integral(h,20),initial_tracked_wet_mass_kg=initial,final_tracked_mass_kg=final,tracked_mass_loss_fraction=(initial-final)/initial)
expected={n for n in config if not n.endswith('_fine')};assert len(expected)==22
if not args.allow_partial:assert set(cases)==expected,sorted(expected-set(cases))
comparisons=[]
for name,x in cases.items():
 if not name.endswith('_expanded'):continue
 base=name.replace('_expanded','_baseline')
 if base not in cases:continue
 b=cases[base];metrics={}
 for k in ['energy_kj','energy_after_20s_kj','peak_hrr_kw','tracked_mass_loss_fraction']:
  metrics[k]=dict(baseline=b[k],expanded=x[k],difference=x[k]-b[k],relative_difference=None if abs(b[k])<1e-9 else (x[k]-b[k])/abs(b[k]))
 comparisons.append(dict(baseline=base,expanded=name,metrics=metrics))
summary=dict(complete=set(cases)==expected,completed_cases=len(cases),expected_nonfine_cases=22,missing=sorted(expected-set(cases)),cases=list(cases.values()),domain_comparisons=comparisons,limitations=['Species-inspired generic fuel geometry; no validated species or bark behavior and no embers.','Imposed 0.4 m 1500 C heating patch for 20 s; not a modeled grass fire.','Tracked wet-particle mass loss includes drying and pyrolysis, not solely combustion.','HRR is simulated combustion heat release, not the imposed heater power.','Fine-grid controls were dropped; grid convergence is not established.','These are pilot measurements, not a trained ten-state model or pristine model validation.'])
out=R/'data/analysis';out.mkdir(exist_ok=True);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('Summarized',len(cases),'verified cases; complete:',summary['complete'])
