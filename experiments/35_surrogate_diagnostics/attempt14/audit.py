"""Read-only raw archive audit: species release and material identifiability. No fitting."""
from pathlib import Path
import json,tarfile,csv,io,re,collections
import numpy as np
R=Path(__file__).resolve().parent; E=R.parents[1]; P=R.parent/'attempt12'
def table(b):
 rows=list(csv.reader(io.StringIO(b.decode())));return rows[1],np.array(rows[2:],float)
out=[]
for ix,item in enumerate(json.loads((P/'inventory.json').read_text())):
 n=item['conditions']['case'];dest=R/'data'/f'{n}.json'
 if dest.exists():out.append(json.loads(dest.read_text()));continue
 d=json.loads((P/'data/states'/f'{n}.json').read_text());deck='';tables={};names=[];version=''
 with tarfile.open(E/item['archive']) as tar:
  for m in tar:
   names.append(m.name)
   if m.name.endswith('.fds'):deck=tar.extractfile(m).read().decode()
   elif m.name.endswith(('_hrr.csv','_devc.csv')):tables[Path(m.name).name]=table(tar.extractfile(m).read())
   elif m.name.endswith('_git.txt'):version=tar.extractfile(m).read().decode().strip()
 hk,h=tables[n+'_hrr.csv'];dk,a=tables[n+'_devc.csv'];t=h[:,0];dt=np.diff(t,prepend=t[0]);mc=float(item['conditions']['moisture'])
 massidx=[j for j,k in enumerate(dk) if k.startswith('v0 mass')];fuelidx=[j for j,k in enumerate(dk) if k.startswith('v0 fuel')]
 mass=a[:,massidx].sum(1);wet0=float(d['snapshots'][0]['remaining_total_material_mass_kg']);dry0=wet0/(1+mc);water0=wet0-dry0
 water_rate=h[:,hk.index('MLR_WATER VAPOR')];lost=np.cumsum(water_rate*dt);remaining=water0-lost
 # Device rates sampled separately: trapezoidal integration is an estimate, not exact interval integration.
 fr=a[:,fuelidx].sum(1);fuel_integral=float(np.trapezoid(fr,a[:,0]));dry_est=dry0-fuel_integral/.75
 s=dict(case=n,source=item['source'],archive=item['archive'],version=version,particle_quantities=d['particle_quantities'][0],csv_columns=hk,device_mass_columns=len(massidx),device_fuel_columns=len(fuelidx),restart_files=[x for x in names if '.restart' in x],moisture_dry_basis=mc,first_device_time_s=float(a[0,0]),first_device_mass_kg=float(mass[0]),first_particle_time_s=d['snapshots'][0]['particle_time_s'],initial_total_mass_kg=wet0,initial_water_estimate_kg=water0,water_emitted_kg=float(lost[-1]),remaining_water_estimate_kg=float(remaining[-1]),min_remaining_water_estimate_kg=float(remaining.min()),water_excess_fraction=float(max(0,-remaining.min())/max(water0,1e-9)),initial_dry_estimate_kg=dry0,device_fuel_vapor_integral_kg=fuel_integral,remaining_unreacted_vegetation_estimate_kg=dry_est,final_total_mass_kg=float(mass[-1]),water_rate_min=float(water_rate.min()),water_rate_max=float(water_rate.max()),fuel_yield_075=bool(re.search(r'NU_SPEC\s*=\s*0\.75',deck)),char_yield_025=bool(re.search(r'NU_MATL\s*=\s*0\.25',deck)),water_specific_device=bool(re.search(r'&DEVC[^/]*WATER',deck,re.S)),source_lines=[x.strip() for x in deck.splitlines() if "&SURF ID='contact burner'" in x])
 dest.write_text(json.dumps(s,indent=2));out.append(s)
 if ix%25==0:print('AUDITED',ix+1,flush=True)
summary=dict(histories=len(out),versions=dict(collections.Counter(x['version'] for x in out)),water_columns=sum('MLR_WATER VAPOR' in x['csv_columns'] for x in out),water_specific_devices=sum(x['water_specific_device'] for x in out),fuel_devices_four=sum(x['device_fuel_columns']==4 for x in out),water_overdraw_gt_1pct=sum(x['water_excess_fraction']>.01 for x in out),water_overdraw_max=max(x['water_excess_fraction'] for x in out),negative_dry_estimates=sum(x['remaining_unreacted_vegetation_estimate_kg']<0 for x in out),yield_matches=sum(x['fuel_yield_075'] and x['char_yield_025'] for x in out),restart_histories=sum(bool(x['restart_files']) for x in out),scope='Initial water split assumes first saved total mass represents initial wet vegetation; water reconstruction from interval release. Dry vegetation from sampled device release /0.75 is provisional, excludes char fuel, and needs numerical closure before training labels.')
res=[x['final_total_mass_kg']-x['remaining_water_estimate_kg']-x['remaining_unreacted_vegetation_estimate_kg'] for x in out]
summary.update(first_particle_time_range_s=[min(x['first_particle_time_s'] for x in out),max(x['first_particle_time_s'] for x in out)],negative_residual_final_solid_mass_count=sum(x<-.01 for x in res),minimum_residual_final_solid_mass_kg=min(res))
(R/'data/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
