"""Compare diagnostics on common time samples; fine grid is a comparator, not truth."""
import json, math, statistics
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from study import ROOT,read_csv,save

def series(folder,name):return read_csv(folder/f'{name}_devc.csv')

def main():
    data=[]
    for p in sorted((ROOT/'data/local').glob('*/result.json')):
        d=json.loads(p.read_text());d['folder']=str(p.parent.relative_to(ROOT));data.append(d)
    comparisons=[]
    for mode in ['flow','fire']:
        fine=next((d for d in data if d['case']==mode+'_fine' and d['full_horizon']),None)
        if not fine:continue
        ref=series(ROOT/fine['folder'],fine['case'])
        times=np.arange(0.1,8.001,.1)
        for d in data:
            if d['mode']!=mode or not d['full_horizon']:continue
            rows=series(ROOT/d['folder'],d['case'])
            metrics={}
            for key in ['surface_max_C','heat_max_kW_m2','wake_u','plume_C']:
                a=np.interp(times,[r['Time'] for r in rows],[r[key] for r in rows])
                b=np.interp(times,[r['Time'] for r in ref],[r[key] for r in ref])
                metrics[key]={'rmse':float(np.sqrt(np.mean((a-b)**2))),'last_4s_mean':float(a[times>=4].mean()),'reference_last_4s_mean':float(b[times>=4].mean()),'max_abs_difference':float(np.max(abs(a-b)))}
            total=d['cpu_profile'].get('Total T_USED (s)',0)
            comparisons.append({'case':d['case'],'repeat':d['repeat'],'cells':d['cells'],'steps':d['steps'],'wall_seconds':d['wall_seconds'],
                'speed_ratio_vs_fine':fine['wall_seconds']/d['wall_seconds'],'metrics':metrics,
                'profile_percent':{k:100*v/total for k,v in d['cpu_profile'].items() if k!='Total T_USED (s)' and total},
                'seconds_per_step':total/d['steps'] if d['steps'] else None})
    verification={}
    h=next((d for d in data if d['case']=='heat_conduction_a'),None)
    if h:
        mu=[brentq(lambda x:x*math.tan(x)-100,n*math.pi+1e-8,n*math.pi+math.pi/2-1e-8) for n in range(100)]
        A=[4*math.sin(m)/(2*m+math.sin(2*m)) for m in mu]
        rows=series(ROOT/h['folder'],h['case'])
        errors=[]
        for r in rows:
            if r['Time']<100:continue
            for name,depth in [('Front',0),('2 cm',.02),('4 cm',.04),('6 cm',.06),('8 cm',.08),('Back',.1)]:
                expected=120-100*sum(a*math.cos(m*(.1-depth)/.1)*math.exp(-m*m*1e-6*r['Time']/.01) for a,m in zip(A,mu))
                errors.append(abs(r[name]-expected))
        verification['slab_conduction']={'time_window_s':[100,2000],'max_abs_error_C':max(errors),'description':'Analytical insulated slab convection solution, Bi=100, alpha=1e-6 m2/s; temperatures from DEVC'}
    p=next((d for d in data if d['case']=='pine_needles'),None)
    if p:
        rows=series(ROOT/p['folder'],p['case']);sums=[r['fuel gas mass']+r['water vapor mass']+r['solid mass'] for r in rows if r['Time']>=.01]
        verification['pine_mass_conservation']={'initial_mass_kg':1,'max_abs_error_kg':max(abs(v-1) for v in sums),'final':rows[-1],'description':'Closed hot box, solid plus evolved fuel and water mass; pyrolysis, not gas-phase flame validation'}
    repeats={}
    for mode in ['flow','fire']:
        ds=[d for d in data if d['case']==mode+'_medium']
        if ds:repeats[mode]={'wall_seconds':[d['wall_seconds'] for d in ds],'max_over_min':max(d['wall_seconds'] for d in ds)/min(d['wall_seconds'] for d in ds)}
    save(ROOT/'results/local_analysis.json',dict(runs=data,comparisons=comparisons,verification=verification,repeats=repeats))
    lines=['# Resolution and profiling study','',f'{len(data)} completed/attempted recorded local runs. All use four OpenMP threads; no early ignition stopping.','',
    'Fine-grid differences measure sensitivity, not validated real-fire error. The 8-second flow/fire windows are transient mechanism screens, not statistically converged LES averages. Local refinement retains fine cells in x=2..6 m and coarsens upstream/downstream only; the finest cells still constrain the global timestep.','',
    '| Case | Cells | Steps | Wall s | Max surface-temperature difference vs fine (C) | Wake velocity RMSE (m/s) |','|---|---:|---:|---:|---:|---:|']
    for c in comparisons:
        if c['repeat']!=1:continue
        lines.append(f"| {c['case']} | {c['cells']} | {c['steps']} | {c['wall_seconds']:.2f} | {c['metrics']['surface_max_C']['max_abs_difference']:.3f} | {c['metrics']['wake_u']['rmse']:.3f} |")
    lines+=['','## Analytical/conservation checks','',json.dumps(verification,indent=2),'','## Timing repeatability','',json.dumps(repeats,indent=2),'','Boundary-file evidence is recorded separately in results/boundary_check.json. No property ignition probability or material validation is claimed.']
    (ROOT/'results/findings.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'run_count':len(data),'verification':verification,'repeats':repeats},indent=2))

if __name__=='__main__':main()
