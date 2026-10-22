"""Read Stage C evidence only after immutable prediction freeze; never refit."""
import hashlib,json,math,subprocess,sys
import numpy as np
from scene import ROOT
from extract_component_states import extract,devices
from component_metrics import metrics
import component_hot_state_model as hot

def main():
 frozen=json.loads((ROOT/'results/component-test-prediction-freeze.json').read_text())
 for p,h in frozen['files'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'Frozen artifact changed'
 assert hashlib.sha256((ROOT/'component_metrics.py').read_bytes()).hexdigest()==frozen['files']['data/component_frozen/component_metrics.py'], 'Metric implementation changed after freeze'
 assert hashlib.sha256((ROOT/'analyze_component_tests.py').read_bytes()).hexdigest()==frozen['files']['data/component_frozen/analyze_component_tests.py'], 'Test analysis changed after freeze'
 cases=json.loads((ROOT/'data/component_frozen/test-inputs.json').read_text())['cases']
 for name in sys.argv[1:]:
  assert name in frozen['cases'];c=next(c for c in cases if c['case']==name);folder=ROOT/'data/cloud'/name;r=json.loads((folder/'result.json').read_text());assert r['deck_sha256']==c['deck_sha256'];raw=extract(c);out=ROOT/'data/component_test_states';out.mkdir(exist_ok=True);(out/(name+'.json')).write_text(json.dumps(raw));ref=hot.series(raw);d=devices(folder,name);end=float(d['Time'][-1]);boundary=ROOT/'data/boundary'/name;boundary.mkdir(exist_ok=True);values=[]
  for face in [-1,1,-2,2,-3,3]:
   p=boundary/f'burn_{face}.csv'
   if not p.exists():
    proc=subprocess.run([str(ROOT.parents[1]/'FDS/install/bin/fds2ascii')],cwd=folder,input=f'{name}\n3\n1\nn\n0 {end}\n{face}\n1\n5\n{p}\n',text=True,capture_output=True,check=True,timeout=120);p.with_suffix('.log').write_text(proc.stdout+proc.stderr)
   for line in p.read_text().splitlines():
    try:v=list(map(float,line.split(',')))
    except ValueError:continue
    if len(v)==4 and math.isfinite(v[3]):values.append(v[3])
  assert values;hit=np.flatnonzero(d['house_burn_max']>1e-9);global_ignition=bool(len(hit));models=[]
  for label in ['graph','baseline','ablation']:
   with np.load(ROOT/'data/component_frozen'/f'{name}-{label}.npz') as a:pred={k:a[k] for k in a.files}
   result=metrics(ref,pred,ref['g']);result.update(reference_whole_structure_ignition=global_ignition,reference_whole_structure_first_burning_s=float(d['Time'][hit[0]]) if len(hit) else None,classification_correct=bool(result['predicted_ignition']==global_ignition) if r['full_horizon'] or global_ignition else None);canopies=[]
   for i,n in enumerate(ref['g']['nodes']):
    if n['kind']=='vegetation':
     nt=len(ref['time']);canopies.append(dict(id=n['id'],initialized=n['initialized'],predicted_fuel_release_kg=float(np.trapezoid(pred['state'][:nt,i,3],ref['time'])/17425),reference_fuel_release_kg=float(np.trapezoid(ref['state'][:,i,3],ref['time'])/17425)))
   models.append(dict(model=label,metrics=result,canopies=canopies))
  report=dict(case=name,full_horizon=r['full_horizon'],physical_seconds=end,wall_seconds=r['wall_seconds'],raw_all_building_boundary_burning_max=max(values),whole_structure_ignition=global_ignition,models=models,limits='Only two preselected90s scenes. Generic wood/vegetation, assigned10/16m canopy patches, artificial20s ignition,0.5m mesh, no trunks/groundcover/embers/interiors. Does not satisfy original16-case/180s coverage criterion. Model predicts sampled patches; full-boundary/global-device reference retains any-part ignition.')
  (ROOT/'results'/f'{name}-test.json').write_text(json.dumps(report,indent=2));print(name,'complete',r['full_horizon'],'FDS ignition',global_ignition)
if __name__=='__main__':main()
