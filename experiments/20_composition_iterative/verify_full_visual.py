"""Verify rerun ignition from device data and raw fds2ascii house boundaries."""
import csv,json,math,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent;W=ROOT/'data/full_visual';C='confirm20_ACG_3200_s4321'
with (W/(C+'_devc.csv')).open() as f:
 r=csv.reader(f);next(r);keys=[x.strip().strip('"') for x in next(r)];rows=[dict(zip(keys,map(float,row))) for row in r if row]
hits=[r['Time'] for r in rows if r['house_burn_max']>1e-9]
values=[];outdir=ROOT/'data/full_visual_boundary';outdir.mkdir(exist_ok=True)
for face in (-1,1,-2,2,-3,3):
 out=outdir/f'burning_{face}.csv'
 answer=f'{C}\n3\n1\nn\n0 90\n{face}\n1\n3\n{out}\n'
 p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=W,input=answer,text=True,capture_output=True,check=True,timeout=60)
 out.with_suffix('.log').write_text(p.stdout+p.stderr)
 for line in out.read_text().splitlines():
  try:v=list(map(float,line.split(',')))
  except ValueError:continue
  if len(v)==4 and math.isfinite(v[3]) and 13.9999<=v[0]<=20.0001 and 9.9999<=v[1]<=14.0001 and -.0001<=v[2]<=4.0001:values.append(v[3])
assert rows[-1]['Time']>=90 and values and (max(values)>1e-12)==bool(hits)
report=dict(first_ignition_s=hits[0] if hits else None,original_ignition_s=9.5052105,house_maximum_0_to_90_mean_burning_rate_kg_m2_s=max(values),boundary_samples=len(values),physical_end_s=rows[-1]['Time'])
(ROOT/'results/full_visual').mkdir(exist_ok=True);(ROOT/'results/full_visual/verification.json').write_text(json.dumps(report,indent=2));print(report)
