"""Exercise exact cloud decoding on retained coverage evidence without training or paid jobs."""
from pathlib import Path
import json,shutil,tempfile
import preprocess_cloud,fields
R=Path(__file__).parent

def main():
 groups=json.loads((R/'groups.json').read_text());g=next(g for g in groups if g['phase']=='coverage');cs=[c for c in json.loads((R/'cases.json').read_text()) if c['case'] in g['cases']]
 assert json.loads((R/'results/coverage-review.json').read_text())['passed']
 with tempfile.TemporaryDirectory(prefix='preprocess-check-',dir=R/'data') as td:
  root=Path(td);(root/'data').mkdir();(root/'results').mkdir();(root/'cases.json').write_text(json.dumps(cs));(root/'groups.json').write_text(json.dumps(groups));shutil.copy2(R/'data/geometries.npz',root/'data/geometries.npz')
  def local_download(key,path):
   name=Path(key).name
   source=R/'data/summaries'/name.replace('.summary.json','.json') if name.endswith('.summary.json') else R/'data/downloads'/name
   shutil.copy2(source,path)
  preprocess_cloud.R=root;preprocess_cloud.download=local_download;fields.ROOT=root;preprocess_cloud.main();audit=json.loads((root/'results/learning-data-audit.json').read_text());assert len(audit)==6
  (R/'results/cloud-data-check.json').write_text(json.dumps(dict(passed=True,cases=audit,scope='Exact cloud decoder on full retained six-case coverage evidence; no model training and no cloud jobs'),indent=2))
 print('Full cloud preprocessing check passed for six coverage cases')
if __name__=='__main__':main()
