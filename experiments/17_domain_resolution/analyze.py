"""Matched-horizon comparisons, pre-ignition curve errors, and particle-mass checks."""
from pathlib import Path
import json,csv
import numpy as np
ROOT=Path(__file__).resolve().parent
summary=json.loads((ROOT/'data/cloud/campaign.json').read_text())
boundary=json.loads((ROOT/'results/boundary.json').read_text())
boundary_burning={r['case']:r for r in boundary['records'] if r['quantity']=='BURNING RATE'}
def series(r):
    with (ROOT/'data/cloud'/r['case']/(r['case']+'_devc.csv')).open() as f:
        it=csv.reader(f);next(it);keys=[s.strip().strip('"') for s in next(it)];a=np.array([list(map(float,row)) for row in it if row])
    return {k:a[:,i] for i,k in enumerate(keys)}
def cpu(r):return r['cpu_user_s']+r['cpu_system_s']
def mass_at_one_second(s):
    return {k:float(np.interp(1.,s['Time'],s[k])) for k in s if k.startswith('mass ')}
comparisons=[];b=summary['bracket']
if b:
    for r in summary['results']:
        if r['phase'] not in ('compare','seedcheck') or not r['full_horizon']:continue
        ref=next(v for k,v in b.items() if isinstance(v,dict) and v['power_kw_m2']==r['power_kw_m2'])
        a,z=series(ref),series(r)
        # Compare exposure before EITHER case ignites; subsequent house fire is a different source.
        end=min([90.]+[v for v in [ref['first_ignition_s'],r['first_ignition_s']] if v is not None])
        times=a['Time'][a['Time']<end];mask=a['Time']<end
        item=dict(case=r['case'],reference=ref['case'],mode=r['mode'],power_kw_m2=r['power_kw_m2'],cpu_speedup=cpu(ref)/cpu(r),wall_speedup=ref['wall_seconds']/r['wall_seconds'],cpu_minutes=cpu(r)/60,ignition_matches=r['ignited']==ref['ignited'],ignited=r['ignited'],first_ignition_s=r['first_ignition_s'],reference_first_ignition_s=ref['first_ignition_s'],preignition_comparison_end_s=end)
        for q in ['house_max','house_flux_max']:
            err=np.interp(times,z['Time'],z[q])-a[q][mask]
            item[q+'_max_abs_error']=float(np.max(np.abs(err)))
            item[q+'_rmse']=float(np.sqrt(np.mean(err**2)))
        # At t=0 FDS reports zero before creating INIT particles. Compare their
        # integrated fuel masses at a common, post-initialization time instead.
        ma,mz=mass_at_one_second(a),mass_at_one_second(z)
        item['fuel_mass_at_1s_kg']=mz
        item['fuel_mass_at_1s_max_abs_difference_kg']=max(abs(mz[k]-ma[k]) for k in ma)
        item['fuel_mass_at_1s_matches']=all(abs(mz[k]-ma[k])<1e-6 for k in ma)
        raw=boundary_burning[r['case']]
        item['raw_boundary_positive_burning_samples']=raw['positive_samples']
        item['raw_boundary_max_window_averaged_burning_rate_kg_m2_s']=raw['maximum_time_averaged_value']
        item['raw_boundary_ignition_matches']=bool(raw['positive_samples'])==bool(r['ignited'])
        comparisons.append(item)
for r in summary['results']:
    s=series(r);r['cpu_minutes']=cpu(r)/60
    m1=mass_at_one_second(s)
    r['fuel_mass_at_1s_kg']=m1
    r['particle_mass_consumed_after_1s_kg']={k:float(m1[k]-s[k][-1]) for k in m1}
mode_summary=[]
for mode in ['mixed','tight','combined','wide']:
    group=[x for x in comparisons if x['mode']==mode]
    if group:mode_summary.append(dict(mode=mode,paired_cases=len(group),ignition_labels_matched=sum(x['ignition_matches'] for x in group),mean_cpu_speedup=float(np.mean([x['cpu_speedup'] for x in group])),cpu_minutes=[x['cpu_minutes'] for x in group],fuel_mass_at_1s_matches=all(x['fuel_mass_at_1s_matches'] for x in group)))
result=dict(campaign_status=summary['status'],error=summary['error'],bracket_relative_width=b['relative_width'] if b else None,bracket_relative_width_target=0.10,bracket_target_met=bool(b and b['relative_width']<=0.10),bracket={k:{'case':v['case'],'power_kw_m2':v['power_kw_m2'],'ignited':v['ignited'],'first_ignition_s':v['first_ignition_s']} for k,v in b.items() if isinstance(v,dict)} if b else None,mode_summary=mode_summary,comparisons=comparisons,runs=summary['results'],raw_boundary_crosschecks=[dict(case=r['case'],device_ignited=r['ignited'],positive_burning_samples=boundary_burning[r['case']]['positive_samples'],max_window_averaged_burning_rate_kg_m2_s=boundary_burning[r['case']]['maximum_time_averaged_value'],label_matches=bool(boundary_burning[r['case']]['positive_samples'])==bool(r['ignited'])) for r in summary['results']],limitations=['90-second horizon; a negative means no ignition during this horizon only.','Synthetic house with prescribed 350 C ignition threshold, not a validated house construction.','Particle properties copied from Douglas-fir validation inputs; changed environment and mesh are not themselves validated.','Source strength is a controlled ignition exposure under two crowns, not wildfire intensity inferred from weather.','The t=0 device sample precedes FDS INIT particle creation; fuel-mass matching is evaluated at 1 s.','Raw BNDF burning-rate results are time-window averages over six structure faces; positive samples support ignition, but zero averages cannot rule out brief temperature threshold crossings.','No ember transport in this benchmark; conclusions concern flame/convection/radiation exposure.','Full-domain 0.5 m reference is a numerical comparator, not demonstrated mesh convergence.'])
(ROOT/'results/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# Domain and resolution comparison','',f"Campaign: {summary['status']}; ignition bracket relative width: {result['bracket_relative_width']:.1%}; 10% target met: {result['bracket_target_met']}",'','| Variant | Paired labels matched | Mean CPU speedup | CPU minutes by endpoint | Fuel mass matched at 1 s |','|---|---:|---:|---:|---|']
for x in mode_summary:lines.append(f"| {x['mode']} | {x['ignition_labels_matched']}/{x['paired_cases']} | {x['mean_cpu_speedup']:.2f}x | {', '.join(f'{v:.2f}' for v in x['cpu_minutes'])} | {x['fuel_mass_at_1s_matches']} |")
lines+=['','| Case | CPU min | CPU speedup | Ignition agrees | Ignition time (reference → case, s) | Max pre-ignition temperature error (°C) |','|---|---:|---:|---|---:|---:|']
for r in comparisons:lines.append(f"| {r['case']} | {r['cpu_minutes']:.2f} | {r['cpu_speedup']:.2f}x | {r['ignition_matches']} | {r['reference_first_ignition_s']} → {r['first_ignition_s']} | {r['house_max_max_abs_error']:.2f} |")
lines+=['','The ignition threshold bracket did not reach its planned 10% relative width; it is reported at the measured width. Raw six-face BNDF burning-rate averages are cross-checked against device ignition labels; see `results/boundary.json` and `analysis.json`.','',*result['limitations']]
(ROOT/'results/findings.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
