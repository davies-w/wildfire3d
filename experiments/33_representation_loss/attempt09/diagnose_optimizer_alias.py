"""No training: test whether optimizer restore shares tensors with saved state."""
from pathlib import Path
import json,torch,copy
from geometry_model import GeometryCNN
R=Path(__file__).parent
s=torch.load(R/'data/resume/current.pt',map_location='cpu',weights_only=False)
a=GeometryCNN();b=GeometryCNN();oa=torch.optim.AdamW(a.parameters());ob=torch.optim.AdamW(b.parameters());oa.load_state_dict(s['optimizer']);ob.load_state_dict(s['optimizer'])
x=next(iter(oa.state.values()));y=next(iter(ob.state.values()));z=next(iter(s['optimizer']['state'].values()))
shared={k:dict(first_second_shared=x[k].data_ptr()==y[k].data_ptr(),first_saved_shared=x[k].data_ptr()==z[k].data_ptr()) for k in x if isinstance(x[k],torch.Tensor)}
ob.load_state_dict(copy.deepcopy(s['optimizer']));y=next(iter(ob.state.values()));isolated=all(y[k].data_ptr()!=z[k].data_ptr() for k in y if isinstance(y[k],torch.Tensor))
assert isolated
(R/'results/optimizer-alias-diagnostic.json').write_text(json.dumps(dict(scope='CPU storage-pointer check only; no optimizer steps. Same-device restore aliases saved state; deepcopy isolates it.',shared=shared,deepcopy_isolated=isolated),indent=2))

# Reproduce the actual pre-training roundtrip used in08/09, not only initial load.
import io
buf=io.BytesIO();torch.save(dict(model=a.state_dict(),optimizer=oa.state_dict()),buf);buf.seek(0);restored=torch.load(buf,map_location='cpu',weights_only=False);oa.load_state_dict(restored['optimizer']);x=next(iter(oa.state.values()));roundtrip={k:x[k].data_ptr()==z[k].data_ptr() for k in x if isinstance(x[k],torch.Tensor)};assert not any(roundtrip.values())
p=R/'results/optimizer-alias-diagnostic.json';result=json.loads(p.read_text());result.update(existing_roundtrip_shares_saved_state=roundtrip,conclusion='Existing pre-training roundtrip breaks initial sharing; no optimizer contamination established. Earlier attribution withdrawn.');p.write_text(json.dumps(result,indent=2))
