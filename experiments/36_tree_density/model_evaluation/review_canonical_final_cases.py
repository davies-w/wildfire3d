"""Descriptive review of the sole already-frozen final model, never model selection."""
from pathlib import Path
import hashlib,json
import numpy as np
from accepted_model_guard import require_accepted_model
from canonical_case_review import review,phase_masks
R=Path(__file__).resolve().parents[1];load=lambda p:json.loads(p.read_text())
def main():
    final=load(R/'results/canonical-final-inference.json');assert final['test_evaluated'] and final['model_frozen_before_test'] and not final['test_used_for_selection'] and final['parameters_unchanged']
    accepted=require_accepted_model(R,trial=final['identity']['trial']);assert accepted['checkpoint_sha256']==final['identity']['checkpoint_sha256']
    protocol=load(R/'results/canonical-final-inference-protocol.json');assert hashlib.sha256((R/'results/canonical-final-inference-protocol.json').read_bytes()).hexdigest()==final['identity']['protocol_sha256']
    for name,digest in protocol['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
    p=R/'data/canonical-final-inference/forecasts.npz';assert hashlib.sha256(p.read_bytes()).hexdigest()==final['forecast_sha256'];saved=np.load(p);ids=saved['source_ids'];assert ids.tolist()==protocol['test_source_ids']
    source=np.load(R/'data/exposure-pilot02/data/sequences.npz');raw=source['state'][ids];configuration=source['configuration'][ids];labels=source['activity_labels'][ids];reports={}
    for h in [1,4,8,16,45]:
        phases={}
        for phase,mask in phase_masks(labels,h).items():
            r=review(saved['candidate_h'+str(h)],saved['baseline_h'+str(h)],raw[:,h:],raw[:,:91-h],configuration,mask)
            for model,key in [('candidate','candidate_MAE'),('baseline','baseline_MAE'),('no_change','no_change_MAE')]:
                expected=final['reports'][model]['canonical'][str(h)]
                expected=expected['model_MAE'] if phase=='overall' else expected['phases'][phase]['model_MAE']
                assert (expected is None and r['pooled'][key] is None) or np.allclose(expected,r['pooled'][key],rtol=2e-5,atol=1e-8)
            phases[phase]=r
        reports[str(h)]=phases
    schema=load(R/'data/exposure-pilot02/schema.json');metadata={str(int(c)):[dict(source_id=int(i),**schema['cases'][int(i)]) for i in ids[configuration==c]] for c in np.unique(configuration)}
    out=dict(simulation_and_partition_scope=protocol['scope'],configuration_metadata=metadata,descriptive_only=True,model_identity=final['identity'],model_or_checkpoint_selection=False,new_acceptance_gates=False,optimizer_updates=0,units=['kg estimated remaining water','kg estimated unreacted dry fuel','kg/s sampled crown gas release, not HRR','K signed surface-heating index, not energy or absolute temperature'],horizons=reports,scope='Every valid stride1 start at each of five horizons. Per-history eligible-origin mean, replica mean within configuration, then equal configuration mean. Counts and worst absolute MAE increases are descriptive; they cannot choose another checkpoint using this test. Phase-empty configurations excluded explicitly; zero baseline error has undefined ratio. Passing pooled gates alone is not proof every case improves, other rotations work, or simplified simulations validate real fire physics.')
    (R/'results/canonical-final-case-review.json').write_text(json.dumps(out,indent=2)+'\n');print('Case/phase review written; no fitting, checkpoint selection or new test-driven gate')
if __name__=='__main__':main()
