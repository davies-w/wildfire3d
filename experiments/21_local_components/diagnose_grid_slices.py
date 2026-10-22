"""Extract actual y18 gas-plane data via fds2ascii; no simulation or causality claim."""
import json,subprocess
import numpy as np
from scene import ROOT
from overnight_grid_v2_control import cases

def run():
 reports=[]
 for c in cases():
  name=c['case'];folder=ROOT/'data/cloud'/name
  if not (folder/'result.json').exists():continue
  end=json.loads((folder/'result.json').read_text())['physical_seconds_reached'];out=ROOT/'data/grid_slice_diagnosis'/name;out.mkdir(parents=True,exist_ok=True)
  # Verify exported ordering against Smokeview metadata before choosing the slice index.
  lines=(folder/(name+'.smv')).read_text().splitlines();slices=[]
  for i,line in enumerate(lines):
   if line.startswith(('SLCF ','SLCC ')):slices.append(dict(header=line,file=lines[i+1].strip(),quantity=lines[i+2].strip()))
  assert len(slices)==5 and slices[2]['quantity']=='TEMPERATURE' and slices[4]['quantity']=='HRRPUV',slices
  for index,quantity in [(3,'TEMPERATURE'),(5,'HRRPUV')]:
   for lo,hi in [(2,4),(4,6),(8,10),(15,20),(22,30),(30,40)]:
    if hi>end:continue
    path=out/f'{quantity}_{lo}_{hi}.csv'
    if not path.exists():
     answer=f'{name}\n2\n1\nn\n{lo} {hi}\n1\n{index}\n{path}\n'
     p=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=answer,text=True,capture_output=True,timeout=120,check=True);path.with_suffix('.log').write_text(p.stdout+p.stderr)
    v=np.loadtxt(path,delimiter=',',skiprows=2);assert v.shape[1]==3
    x,z,q=v.T;mask=(z>=5)&(z<=16)&(abs(x-8)<=3*(1-(z-5)/11));base=mask&(z<=6)
    assert mask.any() and base.any() and np.isfinite(q).all()
    reports.append(dict(case=name,quantity=quantity,plane_y_m=18,average_window_s=[lo,hi],canopy_plane_mean=float(q[mask].mean()),canopy_plane_max=float(q[mask].max()),canopy_base_plane_mean=float(q[base].mean()),canopy_base_plane_max=float(q[base].max()),raw_csv=str(path.relative_to(ROOT))))
 (ROOT/'results/overnight-grid-slice-diagnosis.json').write_text(json.dumps(dict(measurements=reports,limitations='Two-dimensional time-averaged gas-plane samples, not individual particle temperature or total canopy heat release. Values inside the geometric cone envelope include gas gaps. This evidence can locate temperature/reaction differences but cannot alone separate convection, radiation, particle placement and flame feedback.'),indent=2));print('Extracted',len(reports),'plane/window quantities')
if __name__=='__main__':run()
