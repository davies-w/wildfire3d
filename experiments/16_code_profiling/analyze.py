"""Analyze real CPU consumption and sample profiles; no claim of real-fire accuracy."""
import json,csv,re,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def rows(path):
 with path.open() as f:
  r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)]
  return [dict(zip(keys,map(float,v))) for v in r if v]
def main():
 data=[]
 for p in sorted((ROOT/'data/cloud').glob('*/result.json')):
  d=json.loads(p.read_text());d['cpu_total_s']=d['cpu_user_s']+d['cpu_system_s'];d['cpu_per_wall']=d['cpu_total_s']/d['wall_seconds'];d['folder']=str(p.parent.relative_to(ROOT))
  events=[];event_path=p.parent/(d['case']+'_devc_ctrl_log.csv')
  if event_path.exists():
   with event_path.open() as f:
    for e in csv.DictReader(f):
     if e.get('State','').strip()=='T' and e.get('ID','').strip().startswith('house_ignition_'):events.append(float(e['Time (s)']))
  d['first_ignition_event_s']=min(events) if events else None
  d['ignition_label']=True if events else False if d['full_horizon'] else None
  step_path=p.parent/(d['case']+'_steps.csv')
  if step_path.exists():
   with step_path.open() as f:
    next(f);steps=list(csv.DictReader(f))
   d['last_step_time_s']=float(steps[-1]['Simulation Time']);d['steps']=int(steps[-1]['Time Step']);d['fds_cpu_at_last_step_s']=float(steps[-1]['CPU Time']);d['prefix_cost']=[{'simulated_s':float(x['Simulation Time']),'cpu_s':float(x['CPU Time'])} for x in steps]
  if events and d.get('prefix_cost'):
   prefix=d['prefix_cost'];d['estimated_cpu_to_first_ignition_s']=float(np.interp(d['first_ignition_event_s'],[v['simulated_s'] for v in prefix],[v['cpu_s'] for v in prefix]))
  data.append(d)
 by={d['case']:d for d in data};comparisons=[]
 for a,b in [('lot_a','lot_b'),('lot_a','lot_profile'),('hot_a','hot_profile'),('hot_a','hot_passive'),('hot_a','hot_radiation'),('hot_a','hot_coarse')]:
  if a not in by or b not in by:continue
  base,test=by[a],by[b]
  if not base['full_horizon'] or not test['full_horizon']:continue
  comparison={'baseline':a,'candidate':b,'cpu_speedup':base['cpu_total_s']/test['cpu_total_s'],'wall_speedup':base['wall_seconds']/test['wall_seconds'],'devices':{}}
  x=rows(ROOT/base['folder']/f'{a}_devc.csv');y=rows(ROOT/test['folder']/f'{b}_devc.csv')
  ts=np.array([r['Time'] for r in x]);yt=[r['Time'] for r in y]
  for key in x[0]:
   if key=='Time':continue
   xv=np.array([r[key] for r in x]);yv=np.interp(ts,yt,[r[key] for r in y]);comparison['devices'][key]={'max_abs_difference':float(np.max(abs(xv-yv))),'rmse':float(np.sqrt(np.mean((xv-yv)**2)))}
  binary=[]
  for file in sorted((ROOT/base['folder']).iterdir()):
   if file.suffix not in {'.bf','.sf','.prt5'}:continue
   other=ROOT/test['folder']/file.name.replace(a,b,1)
   binary.append({'baseline':file.name,'candidate':other.name,'same_bytes':other.exists() and file.read_bytes()==other.read_bytes(),'baseline_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(other.read_bytes()).hexdigest() if other.exists() else None})
  comparison['binary_evidence']=binary
  comparisons.append(comparison)
 profiles={}
 for d in data:
  f=ROOT/d['folder']/'profile-flat.txt'
  if f.exists():profiles[d['case']]=f.read_text().splitlines()[:45]
 result={'runs':data,'comparisons':comparisons,'profile_excerpt':profiles,'interpretation':'Full horizon required for speed comparisons. Short exposures do not validate full-scenario ignition or 10x feasibility.'}
 (ROOT/'results/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
 lines=['# Code profiling results','', '| Case | Last device/requested simulated s | Wall s | Process CPU s | Mean CPU cores used | Complete |','|---|---:|---:|---:|---:|---|']
 for d in data:lines.append(f"| {d['case']} | {d['physical_seconds_reached']}/{d['horizon_s']} | {d['wall_seconds']:.2f} | {d['cpu_total_s']:.2f} | {d['cpu_per_wall']:.2f} | {d['full_horizon']} |")
 lines+=['','## Paired comparisons','', '| Candidate vs baseline | CPU speedup | Elapsed speedup | Max wall-device difference (C) | Max roof-device difference (C) |', '|---|---:|---:|---:|---:|']
 for c in comparisons:lines.append(f"| {c['candidate']} vs {c['baseline']} | {c['cpu_speedup']:.3f}x | {c['wall_speedup']:.3f}x | {c['devices']['house_wall_max']['max_abs_difference']:.3f} | {c['devices']['house_roof_max']['max_abs_difference']:.3f} |" if 'house_wall_max' in c['devices'] else '')
 lines+=['', 'Speedup is baseline divided by candidate; below 1 means slower. Complete 30-second exposures are screening tests, not validation of ignition outcomes over longer exposures. All detailed device errors and profiles are in analysis.json and profiles/.']
 (ROOT/'results/findings.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'runs':[{k:d[k] for k in ['case','cpu_total_s','wall_seconds','full_horizon']} for d in data],'comparisons':comparisons},indent=2))
if __name__=='__main__':main()
