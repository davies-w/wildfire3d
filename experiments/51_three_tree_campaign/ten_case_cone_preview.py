"""Ten reproducibly selected additional cases; same two cone representations."""
from pathlib import Path
import json,sys,subprocess
import numpy as np
from preview_training import R,ROOT,extract,temperatures,sha
import spatial_training_variants as anchored
import cone_comparison_preview as comparison
from investigate_cone_pivot import search_grid,search_continuous,evaluate
OUT=R/'data/ten-case-cone-preview';BASE=OUT/'base-inputs';INTER=OUT/'anchored-inputs';REPORT=OUT/'fit-report.json'

def main():
 selection=json.loads((R/'ten-case-cone-selection.json').read_text());OUT.mkdir(exist_ok=True)
 sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf
 hf.STATE=R/'private07/ten-case-cone-preservation';hf.STATE.mkdir(exist_ok=True)
 restore=ROOT/'.artifact-staging/ten-case-cone-raw-roundtrip'
 if not (hf.STATE/'restore-verification.json').exists():
  pointers=[str(R/'data/raw-cloud-archives'/(s['archive_key']+'.tar.gz.dvc')) for s in selection['cases']];hf.restore_records(pointers,restore)
 else:assert json.loads((hf.STATE/'restore-verification.json').read_text())['passed']
 report=json.loads(REPORT.read_text()) if REPORT.exists() else {'cases':[]}
 anchored.BASE=BASE;anchored.OUT=INTER;anchored.REPORT=REPORT;comparison.BASE=INTER;comparison.OUT=OUT;comparison.REPORT=REPORT
 for s in selection['cases']:
  case=s['case'];archive=restore/R.relative_to(ROOT)/'data/raw-cloud-archives'/(s['archive_key']+'.tar.gz');assert sha(archive)==s['sha256']
  if not (BASE/case/'metadata.json').exists():extract({'case':case,'archive':str(archive),'sha256':s['sha256'],'HF_restored':True},BASE)
  if not any(x['case']==case for x in report['cases']):
   meta=json.loads((BASE/case/'metadata.json').read_text());domain=meta['domain_m'];shape=np.rint(np.array(domain)/.5).astype(int);center=meta['tree_center_xy_m'];xyz=np.stack(np.meshgrid(*[(np.arange(n)+.5)*.5 for n in shape],indexing='ij'),-1).reshape(-1,3);raw=next((R/'data/completed07').glob('*/'+case+'/solve/'+case+'_1_1.sf'));assert sha(raw)==meta['raw_input_sha256'][raw.name];rows=[]
   for t,a in temperatures(raw,domain,.5):
    temp=a.reshape(-1);points=xyz[temp>50];row={'time_s':t,'active':bool(len(points)),'hot_cells':len(points)}
    if len(points):
     anchor=np.r_[center,0]+meta['static_inputs']['ignition_contact_relative_xyz_m'];c=search_grid(points,anchor[:2],[anchor[2]],range(-180,180,15));free,seeds=search_continuous(points,center,meta['static_inputs']['total_height_m'],domain,True,True);row['fits']={'ignition_apex':evaluate(c,xyz,temp),'plus_horizontal_apex':{**evaluate(free,xyz,temp),'seed_fits':seeds}}
    rows.append(row);print('FIT',case,t,flush=True)
   report['cases'].append({'case':case,'source_temperature_sha256':sha(raw),'frames':rows});REPORT.write_text(json.dumps(report,indent=2)+'\n')
  if not (INTER/case/'cone/metadata.json').exists():anchored.generate(case,kinds=('cone',))
  if not (OUT/case/'animation-verification.json').exists():comparison.generate(case);comparison.render(case)
  print('CASE COMPLETE',case,flush=True)
 print('TEN CASES GENERATED',flush=True)
def finalize():
 for item in json.loads((R/'ten-case-cone-selection.json').read_text())['cases']:
  case=item['case']
  for base in [OUT,INTER]:
   for kind in ['cone','free_cone']:
    p=base/case/kind/'metadata.json'
    if not p.exists():continue
    m=json.loads(p.read_text());m['limits']=m['limits'].replace('tilt restricted to downwind x-z plane, apex searched on tree axis;', 'full 3D direction; anchored tip fixed at ignition location;' if kind=='cone' else 'full 3D direction; free tip bounded to domain x/y and zero-to-tree-height z;');p.write_text(json.dumps(m,indent=2)+'\n')
  for kind in ['cone','free_cone']:
   p=OUT/case/kind;s=json.loads((p/'first-transition.json').read_text());lines=[f'# {case}: {kind}', '',f"Times: {s['initial_state']['time_s']} to {s['next_state']['time_s']} s. Next geometry is interpolated.",'','| State | Unit | Initial | Next |','|---|---|---:|---:|']
   lines += [f'| {n} | {u} | {a:.9g} | {b:.9g} |' for n,u,a,b in zip(s['state_names'],s['state_units'],s['initial_state']['values'],s['next_state']['values'])]
   lines += ['', 'Fixed inputs:', '```json',json.dumps(s['fixed_initial_conditions'],indent=2),'```','No historical state window; see JSON for provenance and interpolation bracket.'];(p/'first-transition.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':
 main();finalize()
