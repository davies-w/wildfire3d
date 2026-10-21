"""Evaluate only after immutable predictions and complete fresh FDS outputs exist."""
from pathlib import Path
import json,hashlib
from datetime import datetime
import numpy as np
from fields import extract
from alignment import align_reference
from snapshot_evaluation import metrics
R=Path(__file__).parent

def main():
 freeze=json.loads((R/'results/prediction-freeze.json').read_text())
 execution=json.loads((R/'jobs/v31-test-0/execution.json').read_text());submitted=datetime.fromisoformat(execution['startTime'].replace('Z','+00:00')).timestamp();assert submitted>freeze['created_unix']
 for n,h in freeze['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
 cs=[c for c in json.loads((R/'cases.json').read_text()) if c['split']=='test'];assert {c['case'] for c in cs}==set(freeze['cases']);rows=[];histories=[];alignment=[]
 for c in cs:
  assert c['deck_sha256']==freeze['test_deck_hashes'][c['case']];result=json.loads((R/'data/cloud'/c['case']/'result.json').read_text());assert result['full_horizon'];extract(c);a=np.load(R/'data/fields'/(c['case']+'.npy'),mmap_mode='r');t=np.load(R/'data/fields'/(c['case']+'-time.npy'))
  wanted=np.load(R/'data/predictions'/('snapshot_'+c['case']+'.npz'))['time'];a,info=align_reference(a,t,wanted);alignment.append(dict(case=c['case'],**info));t=wanted
  for n in ['snapshot','hybrid','state_reset_ablation']:
   pred=np.load(R/'data/predictions'/(n+'_'+c['case']+'.npz'));assert np.max(abs(pred['time']-t))<.1;v=pred['fields'];rows.append(dict(case=c['case'],model=n,**metrics(np.array(a),v,t)));histories.append(dict(case=c['case'],model=n,time_s=t.tolist(),truth_heat_kW=(a[:,1].sum((1,2,3))*.125).tolist(),predicted_heat_kW=(v[:,1].sum((1,2,3))*.125).tolist(),truth_peak_C=a[:,0].max((1,2,3)).tolist(),predicted_peak_C=v[:,0].max((1,2,3)).tolist()))
 (R/'results/fresh-test-evaluation.json').write_text(json.dumps(dict(rows=rows,histories=histories,reference_time_alignment=alignment,frozen_files_verified=len(freeze['files']),fresh_configurations=2,prediction_freeze_unix=freeze['created_unix'],test_submission_unix=submitted,warning='Two configurations in a narrow same-shape height/loading factorial; not broad tree/material/real-world validation'),indent=2));print(json.dumps([{k:r[k] for k in ['case','model','post_source']} for r in rows],indent=2))
if __name__=='__main__':main()
