"""Verify report refactoring preserves published rotation0 and isolates rotation1."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
import importlib.util
R=Path(__file__).resolve().parents[1]
def main():
 paths=list((R/'data/pair-gallery').glob('*'))+[R/f'results/model-pair-{i}-summary.json' for i in (0,1)]
 def hashes():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 before=hashes()
 for name in ('summarize_pair','build_pair_gallery'):
  subprocess.run([sys.executable,str(R/f'model_evaluation/{name}.py')],check=True)
 assert hashes()==before,'Rotation0 changed'
 # Empty isolated root proves collection is required, even after real r1 collection exists.
 with tempfile.TemporaryDirectory() as d:
  for name in ('summarize_pair','build_pair_gallery'):
   spec=importlib.util.spec_from_file_location(name,R/f'model_evaluation/{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.R=Path(d)
   try:
    if name=='summarize_pair':m.summarize(0,1)
    else:m.main(1)
   except FileNotFoundError as e:assert 'pair-sequence-r1-collected.json' in str(e)
   else:raise AssertionError('Uncollected rotation1 accepted')
  assert not list(Path(d).iterdir())
 out=dict(passed=True,rotation0_sha256=before,uncollected_rotation1_refused=True,no_training_or_inference=True)
 (R/'results/pair-reporting-check.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS: published rotation0 unchanged; collection prerequisite enforced')
if __name__=='__main__':main()
