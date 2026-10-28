"""Exact unequal-replica/phase/zero-denominator fixtures; no scientific target loading."""
from pathlib import Path
import hashlib,json,numpy as np
from canonical_case_review import review,phase_masks
R=Path(__file__).resolve().parents[1]
truth=np.zeros((3,3,4));hold=np.ones_like(truth);baseline=np.ones_like(truth)*2;candidate=np.ones_like(truth);candidate[2]=5;configs=np.array([0,0,1]);mask=np.ones((3,3),bool)
r=review(candidate,baseline,truth,hold,configs,mask);assert r['pooled']['candidate_MAE']==[3.]*4 and r['pooled']['baseline_MAE']==[2.]*4
mask[2]=False;r=review(candidate,baseline,truth,hold,configs,mask);assert len(r['configurations'])==1 and r['eligible_histories']==2 and r['pooled']['candidate_MAE']==[1.]*4
mask[:]=False;r=review(candidate,baseline,truth,hold,configs,mask);assert not r['configurations'] and all(v is None for v in r['pooled'].values())
mask[:]=True;r=review(candidate,np.zeros_like(baseline),truth,hold,configs,mask);assert all(row['candidate_over_baseline_MAE']==[None]*4 for row in r['configurations'])
labels=np.array([[0,0,1,2,3,3]]);p=phase_masks(labels,2);assert {k:int(v.sum()) for k,v in p.items()}==dict(overall=5,active=1,quiet=1,weak=1,transition=2)
proof=dict(passed=True,unequal_replicas_equal_configuration_weight_verified=True,empty_phase_and_zero_baseline_handled=True,phase_windows_exact=True,optimizer_updates=0,scientific_targets_loaded=False,source_sha256={n:hashlib.sha256((R/'model_evaluation'/n).read_bytes()).hexdigest() for n in ['canonical_case_review.py','review_canonical_final_cases.py','validate_canonical_case_review.py']})
(R/'results/canonical-case-review-preflight.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
