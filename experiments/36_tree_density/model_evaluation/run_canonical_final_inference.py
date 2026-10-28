"""Single frozen-winner final-test inference; refusal guard precedes test-array loading."""
from pathlib import Path
import fcntl,hashlib,json,sys
import numpy as np
import torch
from accepted_model_guard import require_accepted_model
from inference_verification import evaluate_prefix_pair
from joint_predictor import FrozenJointPredictor
from canonical_metrics import checks
from timing_decoder import JointDecoder
R=Path(__file__).resolve().parents[1];S=R/'data/exposure-pilot02';D=R/'data/canonical-pilot03';load=lambda p:json.loads(p.read_text())
def main():
    with (R/'data/canonical-final-inference.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (R/'results/canonical-final-inference.json').exists(),'Existing test result; never rerun to select a model'
        accepted=require_accepted_model(R,trial='canonical-pilot03') # No test targets may be loaded before this succeeds.
        protocol=load(R/'results/canonical-final-inference-protocol.json');assert protocol['trial']==accepted['trial']
        for name,digest in protocol['source_sha256'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
        identity={k:v for k,v in accepted.items() if k!='snapshot'};identity['protocol_sha256']=hashlib.sha256((R/'results/canonical-final-inference-protocol.json').read_bytes()).hexdigest();identity['test_source_ids_sha256']=protocol['test_source_ids_sha256'];freeze=R/'results/canonical-final-model-freeze.json'
        if freeze.exists():assert load(freeze)==identity,'Frozen model/protocol cannot change after test work begins'
        else:
            with freeze.open('x') as f:json.dump(identity,f,indent=2)
        # The exact winner, checkpoint, source and test IDs are now frozen.
        source=np.load(S/'data/sequences.npz');ids=np.array(protocol['test_source_ids'],dtype=np.int64);assert len(ids)==208 and hashlib.sha256(ids.tobytes()).hexdigest()==protocol['test_source_ids_sha256'];assert (source['fold'][ids]==protocol['test_fold']).all()
        torch.set_num_threads(4);schema=load(S/'schema.json');ck=torch.load(S/'data/initial.pt',map_location='cpu',weights_only=False);initial=torch.load(D/'initial-decoder.pt',map_location='cpu',weights_only=False);sys.path.insert(0,str(S));from model import Transition
        model=Transition('gated');model.load_state_dict(ck['model']);scales=torch.tensor(schema['physical_encoding_scales']);decoder=JointDecoder(initial['feature_mean'],initial['feature_std'],ck['std'],scales,'interval',initial['state_mean']);decoder.load_state_dict(accepted['snapshot']['model']);before={k:v.clone() for k,v in decoder.state_dict().items()};predictor=FrozenJointPredictor(model,ck['mean'],ck['std'],scales,torch.tensor(schema['external_scales']),decoder)
        raw=torch.tensor(source['state'][ids]);times=torch.tensor(source['time'][ids]);configuration=torch.tensor(source['configuration'][ids]);report,arrays=evaluate_prefix_pair(predictor,raw,torch.tensor(source['geometry'][ids]),times,configuration,torch.tensor(source['activity_labels'][ids]),scales,ck['std']);decision=checks(report['baseline'],report['candidate'],protocol['acceptance'],scales.tolist());constraints=report['constraints'];passed=all(decision.values()) and all(constraints[k] for k in ['finite','mass_nonnegative','gas_nonnegative','coherent_mass_nonincreasing'])
        assert all(torch.equal(v,before[k]) for k,v in decoder.state_dict().items()) and all(torch.equal(v,ck['model'][k]) for k,v in model.state_dict().items());assert load(freeze)==identity
        folder=R/'data/canonical-final-inference';folder.mkdir(exist_ok=True);destination=folder/'forecasts.npz';assert not destination.exists(),'Preserved forecasts require diagnosis before resuming'
        with destination.open('xb') as f:np.savez_compressed(f,source_ids=ids,**{k:v.numpy() for k,v in arrays.items()})
        out=dict(passed=passed,test_evaluated=True,optimizer_updates=0,model_frozen_before_test=True,test_used_for_selection=False,parameters_unchanged=True,test_histories=len(ids),test_configurations=len(torch.unique(configuration)),identity=identity,checks=decision,reports=report,forecast_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),full_goal_complete=False,scope='Existing rotation0test-set actual-prefix inference only, with no model/threshold changes after outcomes. Passing this is evidence for this fixed pipeline/split, not other rotations, physical realism, or automatic deployment. All phase tables, actual durations, raw/no-change comparators and coherent-forecast constraints retained. Stitched display increases are revisions; projected negative observed water boundary is explicit; heating remains signed.')
        (R/'results/canonical-final-inference.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='reports'},indent=2))
if __name__=='__main__':main()
