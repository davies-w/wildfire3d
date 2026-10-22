"""Load frozen checkpoints, then confirmation inputs; never read FDS test output."""
import hashlib,json,time
import torch
from models import ROOT,batch,model

def main():
    dest=ROOT/'results/frozen-predictions.json'
    if dest.exists():raise RuntimeError('Predictions already frozen')
    weights_path=ROOT/'results/frozen-weights.json'
    weights=json.loads(weights_path.read_text())
    inputs_path=ROOT/'data/cloud/confirmation-inputs.json'
    tests=json.loads(inputs_path.read_text());assert len(tests)==12
    assert all(0<r['total_source_kw']<=3200 and r['seed'] in (4321,5678) for r in tests)
    torch.set_num_threads(1)
    start=time.perf_counter();features=batch(tests);preprocess=(time.perf_counter()-start)/12
    outputs=[]
    for record in weights['models']:
        checkpoint=ROOT/record['checkpoint']
        assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()==record['checkpoint_sha256']
        m=model(record['kind']);m.load_state_dict(torch.load(checkpoint,weights_only=True));m.eval()
        with torch.inference_mode():
            heads,aux=m(*features);probs=torch.sigmoid(heads[:,0]).tolist()
            times=torch.nn.functional.softplus(heads[:,1]).mul(90).tolist()
            for _ in range(20):m(*features)
            start=time.perf_counter()
            for _ in range(100):m(*features)
            elapsed=(time.perf_counter()-start)/1200
        outputs.append(dict(record,inference_seconds_per_case=elapsed,predictions=[dict(case=r['case'],
            ignition_probability=p,time_prediction_s=t,auxiliary=a) for r,p,t,a in zip(tests,probs,times,aux.tolist())]))
    dest.write_text(json.dumps(dict(created_unix=time.time(),test_labels_read=False,
        frozen_weights_sha256=hashlib.sha256(weights_path.read_bytes()).hexdigest(),
        confirmation_inputs_sha256=hashlib.sha256(inputs_path.read_bytes()).hexdigest(),
        preprocessing_seconds_per_case=preprocess,models=outputs),indent=2)+'\n')
    print('Saved immutable confirmation predictions; no confirmation FDS outputs read.')
if __name__=='__main__':main()
