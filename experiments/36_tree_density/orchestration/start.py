"""One-time handoff to cloud; refuses ambiguous or duplicate submissions."""
from pathlib import Path
import sys,json,fcntl,time,yaml,hashlib
R=Path(__file__).resolve().parent.parent;O=R/'orchestration';sys.path.insert(0,str(R));from cloud import gc,B
with (R/'data/dispatcher.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (O/'cloud-owner.json').exists()
 assert json.loads((O/'deployment-complete.json').read_text())['groups']==102
 assert json.loads((O/'spec-upload-complete.json').read_text())['verified']==102
 assert not gc('batch','jobs','list','--location=us-central1')
 assert not gc('compute','instances','list')
 globalq={q['metric']:q for q in gc('compute','project-info','describe')['quotas']};rq={q['metric']:q for q in gc('compute','regions','describe','us-central1')['quotas']}
 assert globalq['CPUS_ALL_REGIONS']['limit']>=80 and rq['C3_CPUS']['limit']>=80 and rq['IN_USE_ADDRESSES']['limit']>=20 and rq['SSD_TOTAL_GB']['limit']>=600
 gs=json.loads((O/'queue.json').read_text());gc('artifacts','docker','images','describe',gs[0]['image_uri'])
 assert yaml.safe_load(gc('workflows','describe','fds-density36-parent','--location=us-central1')['sourceContents'])==yaml.safe_load((O/'parent-inline.yaml').read_text())
 assert not gc('workflows','executions','list','fds-density36-parent','--location=us-central1')
 with (B.parent/'data/budget.lock').open('w') as f:
  fcntl.flock(f,fcntl.LOCK_EX);b=json.loads(B.read_text());assert b['estimated_spend_usd']+b['reserved_usd']<=125
  for g in gs:
   e=b['reservations'][g['id']];assert e['state']=='reserved_before_upload';e['state']='delegated_to_cloud_queue';e['cloud_workflow']='fds-density36-parent'
  b['reservations']['density36-cloud-orchestration']['state']='submission_pending';B.write_text(json.dumps(b,indent=2)+'\n')
 owner={'state':'submission_pending','workflow':'fds-density36-parent','groups':102,'cases':sum(len(g['cases']) for g in gs),'local_submissions_disabled':True,'submitted_unix':time.time(),'parent_source_sha256':hashlib.sha256((O/'parent-inline.yaml').read_bytes()).hexdigest()}
 (O/'cloud-owner.json').write_text(json.dumps(owner,indent=2)+'\n')
 e=gc('workflows','execute','fds-density36-parent','--location=us-central1');(O/'execution.json').write_text(json.dumps(e,indent=2)+'\n');owner.update(state='submitted',execution=e['name']);(O/'cloud-owner.json').write_text(json.dumps(owner,indent=2)+'\n');print(e['name'],flush=True)
