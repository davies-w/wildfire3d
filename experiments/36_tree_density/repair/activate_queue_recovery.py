"""Activate explicitly approved queue replacements without launching compute."""
from pathlib import Path
import json,hashlib,lzma,fcntl,time
R=Path(__file__).resolve().parent.parent
B=R.parent/'33_representation_loss/budget.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 with (R/'data/dispatcher.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  old=json.loads((R/'restored-groups.json').read_text());new=json.loads((R/'proposed-queue-recovery-groups.json').read_text())
  assert len(new)==131 and sum(len(g['cases']) for g in new)==1560
  changed=[]
  for a,g in zip(old,new):
   if a==g:continue
   assert g['id']==a['id']+'-r1' and a['cases']==g['cases']
   proof=json.loads((R/'jobs'/a['id']/'terminal-no-results.json').read_text())
   assert proof['run_duration_s']==0 and proof['cleanup_verified'] and proof['grant_removed']
   blob=(R/g['package_file']).read_bytes();assert sha(blob)==g['package_sha256']
   assert sha((R/'jobs'/g['id']/g['workflow_file']).read_bytes())==g['workflow_sha256']
   x=json.loads(lzma.decompress((R/a.get('package_file','data/packages/'+a['id']+'.xz')).read_bytes()));y=json.loads(lzma.decompress(blob))
   xx=json.loads(x.pop('group.json'));yy=json.loads(y.pop('group.json'));yy['id']=xx['id'];assert x==y and xx==yy
   changed.append(g)
  assert len(changed)==12
  with (B.parent/'data/budget.lock').open('w') as budget_lock:
   fcntl.flock(budget_lock,fcntl.LOCK_EX);b=json.loads(B.read_text())
   missing=[g for g in changed if g['id'] not in b['reservations']]
   addition=round(.4*len(missing),2)
   assert b['estimated_spend_usd']+b['reserved_usd']+addition<=b['authorized_usd']
   for g in missing:b['reservations'][g['id']]=dict(state='reserved_before_upload',allowance_usd=.4,cases=len(g['cases']),reserved_unix=time.time(),authorization='User explicitly approved replacement groups and continuation; subsequently authorized necessary overnight repairs within budget')
   b['reserved_usd']=round(b['reserved_usd']+addition,2)
   B.write_text(json.dumps(b,indent=2)+'\n')
  (R/'active-groups.json').write_bytes((R/'proposed-queue-recovery-groups.json').read_bytes())
  proof=dict(activated=True,approved=True,replacement_groups=12,replacement_allowance_usd=4.8,old_allowances_retained=True,scientific_payload_equivalence_verified=True,active_manifest_sha256=sha((R/'active-groups.json').read_bytes()),new_compute_launched=False)
  (R/'results/queue-recovery-activation.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
