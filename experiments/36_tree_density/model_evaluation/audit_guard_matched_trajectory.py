"""Fit-only convergence diagnostic; no optimizer updates or holdout scoring."""
from pathlib import Path
import sys,json,hashlib
import torch
R=Path(__file__).resolve().parents[1];D=R/'data/guard-matched-pilot01';O=R/'data/guard-matched-pilot01-results';sys.path.insert(0,str(D))
from guard_matched_data import GuardMatchedData
from joint_decoder import JointDecoder
from joint_metrics import score_prediction
assert json.loads((R/'results/guard-matched-pilot01-analysis.json').read_text())['passed']
torch.set_num_threads(4);d=GuardMatchedData(D);ids=d.roles['fit'];initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False)
m=JointDecoder(initial['feature_mean'],initial['feature_std'],d.std,d.scales,'interval',initial['state_mean'])
args=(d.raw[ids],d.times[ids],d.config[ids],d.labels[ids],d.scales,d.std)
rows=[]
with torch.inference_mode():
 baseline=d.predictions(None,ids);base=[score_prediction(baseline[i],*args,display=i==1) for i in range(2)]
 for epoch in [0,50,100,150,200,250,300]:
  state=initial['model'] if epoch==0 else torch.load(O/f'balanced_tail-epoch{epoch:03}.pt',map_location='cpu',weights_only=False)['model']
  m.load_state_dict(state);before={k:v.clone() for k,v in m.state_dict().items()};prediction=d.predictions(m,ids);scores=[score_prediction(prediction[i],*args,display=i==1) for i in range(2)]
  rows.append(dict(epoch=epoch,ratios={name:[a/b for a,b in zip(scores[i]['physical_MAE_by_feature'],base[i]['physical_MAE_by_feature'])] for i,name in enumerate(['autonomous','display'])},startup_ratio=scores[0]['startup_gas_p90_deficit']/base[0]['startup_gas_p90_deficit']))
  assert all(torch.equal(v,before[k]) for k,v in m.state_dict().items())
assert not d.confirmation_open
out=dict(passed=True,arm='balanced_tail',optimizer_updates=0,fit_histories=len(ids),rows=rows,confirmation_and_test_not_used=True,scope='Retrospective fit trajectory, not checkpoint selection or evidence of generalization. Finite epoch samples cannot establish convergence or a capacity bound.',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(R/'results/guard-matched-fit-trajectory.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
