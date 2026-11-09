"""Validate the 22 pre-existing scenario aliases without changing inputs or labels."""
from pathlib import Path
import json,gzip,hashlib
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=json.loads((R.parent/'49_compact_tree_domain/data/cases.json').read_text())+json.loads((R.parent/'50_live_oak/data/pilot/cases.json').read_text());rows=[]
 for c in map(json.loads,gzip.open(R/'data/cases.jsonl.gz','rt')):
  if not c.get('reuse'):continue
  reuse=c['reuse'];p=ROOT/reuse['proof_path'];proof=json.loads(p.read_text());assert digest(p)==reuse['proof_sha256'] and proof['passed'] and proof['physical_time_s']==180 and proof['deck_sha256']==reuse['deck_sha256']
  old=next(x for x in prior if x['pilot_case']==reuse['case']);keys=['geometry_id','ignition_index','wind_m_s','moisture_fraction','loading_multiplier'];assert all(c[k]==old[k] for k in keys)
  rows.append({'target_case':c['case']+'_baseline','source_case':reuse['case'],'proof_path':reuse['proof_path'],'proof_sha256':reuse['proof_sha256'],'matching_parameters':{k:c[k] for k in keys},'source_design':old,'source_filename_alias_required':True})
 assert len(rows)==22
 out=R/'private07/reused-training-source-map.json';out.write_text(json.dumps({'passed':True,'count':22,'conversion_complete':False,'cases':rows},indent=2)+'\n');print('PASS:22 source mappings, exact design signatures and pinned original proofs; conversion still pending')
if __name__=='__main__':main()
