"""Scoped preservation of the authorized ten-case cone preview; no deletion."""
import sys,json,yaml,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'scripts'));import dvc_hf as hf

def depfile(d):
 p=R/d
 if p.exists():return p
 return ROOT/'.artifact-staging/conifer-input-roundtrip'/R.relative_to(ROOT)/d

def main():
 subprocess.run([str(ROOT/'.venv/bin/python'),str(R/'validate_conifer_cones.py')],check=True)
 stage='conifer_cone_preview';p=R/'dvc.yaml';doc=yaml.safe_load(p.read_text());deps=['conifer_cone_preview.py','restore_conifer_inputs.py','validate_conifer_cones.py','preserve_conifer_cones.py','conifer-cone-selection.json','cone_comparison_preview.py','spatial_training_variants.py','preview_training.py','investigate_cone_pivot.py','interpolate_cone_labels.py','data/cases.jsonl.gz','data/geometries.json','data/decks/cases.json','../36_tree_density/material_reader.py','../36_tree_density/fortran_records.py']
 for s in json.loads((R/'conifer-cone-selection.json').read_text())['cases']:
  c=s['case'];folder=R/s['solve'];deps.extend(str((folder/n).relative_to(R)) for n in ['input.fds',c+'_1.prt5',c+'_hrr.csv',c+'_devc.csv',c+'_1_1.sf',c+'.smv']);deps.append(s['proof'])
 doc['stages'][stage]={'cmd':'../../.venv/bin/python conifer_cone_preview.py && ../../.venv/bin/python validate_conifer_cones.py','frozen':True,'deps':deps,'outs':['data/conifer-cone-preview']};p.write_text(yaml.safe_dump(doc,sort_keys=False))
 hf.STATE=R/'private07/conifer-cone-output-preservation';hf.STATE.mkdir(exist_ok=True);hf.stage_commit(str(p)+':'+stage)
 lp=R/'dvc.lock';lock=yaml.safe_load(lp.read_text());lock['stages'][stage]['deps']=[{'path':d,'hash':'md5','md5':hashlib.md5(depfile(d).read_bytes()).hexdigest(),'size':depfile(d).stat().st_size} for d in deps];lp.write_text(yaml.safe_dump(lock,sort_keys=False))
 plan=json.loads((hf.STATE/'plan.json').read_text());print('Scoped generated data plan',len(plan['objects']),'objects',flush=True);hf.upload(hf.STATE/'plan.json')
 rec=lock['stages'][stage]['outs'][0].copy();rec['path']=str(R/rec['path']);pointer=hf.STATE/'roundtrip.dvc';pointer.write_text(yaml.safe_dump({'outs':[rec]}));hf.restore_records([str(pointer)],ROOT/'.artifact-staging/conifer-cone-output-roundtrip');print('PRESERVED AND RESTORED',flush=True)
if __name__=='__main__':main()
