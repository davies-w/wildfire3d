"""Freeze repaired rotation0 and conditional rotation1 in one cloud supervisor."""
from pathlib import Path
import json,hashlib,io,tarfile,base64,shutil,yaml
R=Path(__file__).resolve().parents[1];D=R/'data/pair-sequence';SRC=R/'data/model-pair-training';BUCKET='tmrw-wildfire-20261015-trial';PROJECT='tmrw-wildfire-20261015';PREFIX='density36/pair-sequence01/'
def http(method,url,result=None,query=None,body=None):
 d={'call':'http.'+method,'args':{'url':url,'auth':{'type':'OAuth2'}}}
 if query is not None:d['args']['query']=query
 if body is not None:d['args'].update(body=body,headers={'Content-Type':'application/json'})
 if result:d['result']=result
 return d
def main():
 assert json.loads((R/'results/model-pair-training-failure.json').read_text())['no_real_training_started']
 D.mkdir(exist_ok=True);proofs=[];subs={};original=json.loads((R/'results/model-pair-training-prepared.json').read_text())
 fixed=(SRC/'check_resume.py').read_text().replace('torch.equal(p[k],q[k])','torch.equal(p[k].detach().cpu(),q[k].detach().cpu())');assert fixed!=(SRC/'check_resume.py').read_text();compile(fixed,'fixed-resume-check','exec')
 fullmeta=json.loads((R/'learning-schema.json').read_text())
 for rotation in (0,1):
  T=D/f'rotation{rotation}';(T/'data').mkdir(parents=True,exist_ok=True);prefix=PREFIX+f'rotation{rotation}/';label=f'gpu36-seq01-r{rotation}';names=list(original['files'])
  for n in names:shutil.copyfile(SRC/n,T/n)
  (T/'check_resume.py').write_text(fixed);(T/'runtime.py').write_text((SRC/'runtime.py').read_text().replace('density36/model-pair-training01/',prefix))
  meta=json.loads((SRC/'schema.json').read_text());meta['rotations']=[fullmeta['rotations'][rotation]];meta['comparison']=f'Matched plain and soft-gated stride-one pair, fixed rotation{rotation}';(T/'schema.json').write_text(json.dumps(meta,indent=2)+'\n')
  p=json.loads((SRC/'coverage-plan.json').read_text());p.update(experiment=f'Density36 matched stride-one pair rotation{rotation}',test=f'Shared fixed rotation{rotation} test fold');(T/'coverage-plan.json').write_text(json.dumps(p,indent=2)+'\n')
  # Identical science/worker and model modules; only rotation/schema, prefix, labels and diagnostic comparison differ.
  for n in ('worker.py','plain_model.py','gated_model.py','model.py','data/sequences.npz'):assert (T/n).read_bytes()==(SRC/n).read_bytes()
  rot=meta['rotations'][0];sets=[set(rot[k]) for k in ('train','validation','test')];assert set.union(*sets)==set(range(2080)) and all(sets[i].isdisjoint(sets[j]) for i,j in ((0,1),(0,2),(1,2)))
  hashes={n:hashlib.sha256((T/n).read_bytes()).hexdigest() for n in names}
  with tarfile.open(T/'inputs.tar','w') as tar:
   for n in names:
    b=(T/n).read_bytes();i=tarfile.TarInfo(n);i.size=len(b);tar.addfile(i,io.BytesIO(b))
   b=json.dumps(hashes,sort_keys=True).encode();i=tarfile.TarInfo('hashes.json');i.size=len(b);tar.addfile(i,io.BytesIO(b))
  boot=(SRC/'bootstrap.py').read_text().replace('density36/model-pair-training01/',prefix)
  w=json.loads(json.dumps(yaml.safe_load((SRC/'workflow.yaml').read_text())).replace('gpu36-pairtrain01',label).replace('density36/model-pair-training01/',prefix))
  w['main']['steps'][0]['initialize']['assign'][1]['job']['taskGroups'][0]['taskSpec']['runnables'][0]['container']['commands']=['-c',"import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(boot.encode()).decode())+"),'bootstrap','exec'))"]
  subs[f'rotation{rotation}']=w['main'];(T/'bootstrap.py').write_text(boot);(T/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
  proofs.append(dict(rotation=rotation,prefix=prefix,label=label,input_sha256=hashlib.sha256((T/'inputs.tar').read_bytes()).hexdigest(),input_bytes=(T/'inputs.tar').stat().st_size,files=hashes,train_histories=len(rot['train']),validation_histories=len(rot['validation']),test_histories=len(rot['test']),maximum_allowance_usd=15.2))
 storage='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/';upload='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o'
 steps=[{'lease':http('post',upload,query={'uploadType':'media','name':PREFIX+'lease.json','ifGenerationMatch':'0'},body={'purpose':'Exactly one execution owns both fixed rotations','reserved_training_usd':30.4})},
 {'first':{'call':'rotation0','result':'first_result'}},
 {'require_success':{'switch':[{'condition':'${first_result.final_state != "SUCCEEDED"}','raise':'First pair failed; no automatic retry or next rotation'}]}},
 {'completion_metadata':http('get',storage+'density36%2Fpair-sequence01%2Frotation0%2Fcomplete.json','complete_metadata')},
 {'completion':http('get',storage+'density36%2Fpair-sequence01%2Frotation0%2Fcomplete.json','complete',{'alt':'media'})},
 {'decode_complete':{'call':'decode_document','args':{'value':'${complete.body}'},'result':'complete_doc'}},
 {'freeze':http('get',storage+'density36%2Fpair-sequence01%2Frotation0%2Fselection-freeze.json','freeze',{'alt':'media'})},
 {'decode_freeze':{'call':'decode_document','args':{'value':'${freeze.body}'},'result':'freeze_doc'}},
 {'validate_completion':{'switch':[{'condition':'${complete_doc.success != true or complete_doc.folds != 2 or len(freeze_doc.selected) != 2 or freeze_doc.test_not_evaluated_yet != true}','raise':'Incomplete matched pair; no next rotation'}]}},
 {'morning_gate':{'switch':[{'condition':'${time.parse(complete_metadata.body.timeCreated) >= time.parse("2026-10-27T15:00:00Z")}','next':'skip_next'}]}},
 {'cleanup_deadline':{'assign':[{'cleanup_until':'${sys.now() + 600}'}]}},
 {'check_jobs':http('get','https://batch.googleapis.com/v1/projects/'+PROJECT+'/locations/us-central1/jobs','jobs')},
 {'check_vms':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-central1-c/instances','vms')},
 {'check_disks':http('get','https://compute.googleapis.com/compute/v1/projects/'+PROJECT+'/zones/us-central1-c/disks','disks')},
 {'cleanup_gate':{'switch':[{'condition':'${len(default(map.get(jobs.body,"jobs"),[])) == 0 and len(default(map.get(vms.body,"items"),[])) == 0 and len(default(map.get(disks.body,"items"),[])) == 0}','next':'second'},{'condition':'${sys.now() >= cleanup_until}','raise':'Resources remain after first pair; next rotation not launched'}]}},
 {'cleanup_sleep':{'call':'sys.sleep','args':{'seconds':30},'next':'check_jobs'}},
 {'second':{'call':'rotation1','result':'second_result'}},
 {'require_second_success':{'switch':[{'condition':'${second_result.final_state != "SUCCEEDED"}','raise':'Second pair failed; no automatic retry'}]}},
 {'record_finished':http('post',upload,query={'uploadType':'media','name':PREFIX+'sequence-complete.json','ifGenerationMatch':'0'},body={'first':'${first_result}','second':'${second_result}','next_rotation_started':True})},
 {'done':{'return':{'first':'${first_result}','second':'${second_result}','next_rotation_started':True}}},
 {'skip_next':http('post',upload,query={'uploadType':'media','name':PREFIX+'sequence-complete.json','ifGenerationMatch':'0'},body={'first':'${first_result}','next_rotation_started':False,'reason':'First pair completed after08:00Pacific cutoff'})},
 {'skipped':{'return':{'first':'${first_result}','next_rotation_started':False,'reason':'Morning cutoff'}}}]
 decode={'params':['value'],'steps':[{'already_decoded':{'switch':[{'condition':'${get_type(value) == "map"}','return':'${value}'}]}},{'decode':{'return':'${json.decode(value)}'}}]}
 w={'main':{'steps':steps},'decode_document':decode,**subs};(D/'workflow.yaml').write_text(yaml.safe_dump(w,sort_keys=False))
 report=dict(prepared=True,submitted=False,workflow='fds-gpu36-pair-sequence01',cutoff_utc='2026-10-27T15:00:00Z',reserved_training_usd=30.4,maximum_pairs=2,automatic_retries=0,workflow_sha256=hashlib.sha256((D/'workflow.yaml').read_bytes()).hexdigest(),packages=proofs,repair='Only synthetic optimizer-state comparison moved toCPU, no model/training changes',laptop_independent=True)
 (R/'results/pair-sequence-prepared.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='packages'}))
if __name__=='__main__':main()
