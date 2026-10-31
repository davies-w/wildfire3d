"""Forward-only CPU proof for both recurrent memories; no optimizer or backward."""
from pathlib import Path
import ast,json,hashlib,importlib.util,io,torch,yaml
R=Path(__file__).resolve().parent;D=R/'data/training';torch.set_num_threads(4)
spec=importlib.util.spec_from_file_location('stacked',D/'gated_model.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
torch.manual_seed(3516);m=mod.Transition('gated');assert sum(p.numel() for p in m.parameters())==50119
assert not any(isinstance(v,torch.nn.Dropout) for v in m.modules())
assert torch.count_nonzero(m.head.weight)==0 and torch.count_nonzero(m.head.bias)==0
assert torch.all(m.gate_head.bias==4) and torch.count_nonzero(m.gate_head.weight)==0
# Extract exactly the worker's prefix functions without importing CUDA/training code.
tree=ast.parse((R/'worker.py').read_text());ns=dict(torch=torch,external=torch.randn(6,90,9))
exec(compile(ast.Module(body=[v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name in ['history_at','prefix_memory']],type_ignores=[]),'<prefix-only>','exec'),ns)
with torch.no_grad():
 x=torch.randn(6,90,41);whole,final=m.cell(x);states=m.cell.prefix_states(x);mem=None;out=[]
 for j in range(90):
  yy,mem=m.cell(x[:,j:j+1],mem);out.append(yy)
  assert torch.allclose(mem,states[:,j].transpose(0,1),atol=2e-6,rtol=2e-5)
 assert torch.allclose(torch.cat(out,1),whole,atol=2e-6,rtol=2e-5) and torch.allclose(mem,final,atol=2e-6,rtol=2e-5)
 z=torch.randn(6,91,4);ids=torch.arange(6);js=torch.tensor([0,1,7,32,64,89]);prefix=ns['prefix_memory'](m,z,ids,js);assert prefix.shape==(2,6,64) and not prefix.requires_grad
 for b,j in enumerate(js.tolist()):
  expected=torch.zeros(2,1,64)
  for step in range(j):
   hist=ns['history_at'](z,ids[b:b+1],torch.tensor([step]));_,expected=m.cell(m.inputs(hist,ns['external'][b:b+1,step])[:,None],expected)
  assert torch.allclose(prefix[:,b:b+1],expected,atol=2e-6,rtol=2e-5)
  changed=z.clone();changed[b,j+1:]+=1000
  assert torch.equal(prefix,ns['prefix_memory'](m,changed,ids,js)),'Future truth influenced prefix'
 m.head.weight.fill_(.001);history=torch.randn(6,8,4);external=torch.randn(6,9);pred,mem=m.step(history,external,prefix)
 assert mem.shape==(2,6,64) and torch.isfinite(pred).all()
 buf=io.BytesIO();torch.save(m.state_dict(),buf);buf.seek(0);other=mod.Transition('gated');other.load_state_dict(torch.load(buf,weights_only=True))
 p2,m2=other.step(history,external,prefix);assert torch.equal(pred,p2) and torch.equal(mem,m2)
p=json.loads((D/'coverage-plan.json').read_text());assert 'continuation' not in p and p['minimum_epochs']==160 and p['dropout_probability']==0 and p['recurrent_layers']==2
assert p['horizon_curriculum']==[dict(first_epoch=e,steps=h) for e,h in [(1,1),(21,8),(41,16),(61,32),(110,64),(130,90)]]
assert not (D/'data/resume').exists()
schema=json.loads((D/'schema.json').read_text());rot=schema['rotations'][0];assert rot['rotation']==0 and [len(rot[k]) for k in ['train','validation','test']]==[1662,210,208]
keys=[{tuple(schema['cases'][i]['physical_key']) for i in rot[k]} for k in ['train','validation','test']]
assert len(keys[2])==204 and not (keys[0]&keys[1] or keys[0]&keys[2] or keys[1]&keys[2])
for n,h in json.loads((D/'hashes.json').read_text()).items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
for f in [*R.glob('*.py'),*D.glob('*.py')]:ast.parse(f.read_text())
cs=yaml.safe_load((R/'pool01.yaml').read_text())['main']['steps'][0]['initialize']['assign'][0]['candidates'];assert len(cs)==3
for c in cs:
 q=c['job']['allocationPolicy']['instances'][0]['policy'];t=c['job']['taskGroups'][0]['taskSpec'];assert q['provisioningModel']=='SPOT' and q['machineType']=='n1-standard-4' and q['accelerators']==[dict(type='nvidia-tesla-t4',count=1)] and t['maxRetryCount']==0
proof=dict(passed=True,parameters=50119,recurrent_layers=2,memory_shape='2,batch,64',dropout=0,fresh_initialization=True,no_resume_artifacts=True,both_layer_prefix_equivalence=True,variable_origin_prefix_equivalence=True,no_future_truth=True,serialization_bitwise=True,split_configuration_disjoint=True,optimizer_executed=False,cloud_backward_still_required=True)
(R/'validation.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
