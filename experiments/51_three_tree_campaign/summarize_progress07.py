"""Summarize independently collected successes and pinned interruption evidence."""
from cloud07 import *
proofs=json.loads((P/'worker-proofs.json').read_text())
outcomes=[x for x in proofs if x['name'].startswith(PREFIX+'outcomes/') and not x['proof']['passed']]
spot=[];deferred=[];recreated=[];other_failed=[]
for x in outcomes:
 outcome=x['proof'];wave=outcome['wave']
 if outcome.get('spot'):
  tasks=[v for v in proofs if v['name']==PREFIX+wave+'/failed-task.json'];assert len(tasks)==1
  events=tasks[0]['proof']['tasks'][0]['status']['statusEvents'];assert any(e.get('taskExecution',{}).get('exitCode')==50001 for e in events)
  spot.append(wave)
 elif outcome.get('admission_deferred'):deferred.append(wave)
 else:
  task=next((v['proof'] for v in proofs if v['name']==PREFIX+wave+'/failed-task.json'),{})
  events=[e for t in task.get('tasks',[]) for e in t.get('status',{}).get('statusEvents',[])]
  if any(e.get('taskExecution',{}).get('exitCode')==50006 and 'VM is recreated during task execution' in e.get('description','') for e in events):recreated.append(wave)
  else:other_failed.append(wave)
# An epoch can end before it publishes a child's outcome. The immutable terminal
# task record is sufficient to identify the infrastructure interruption itself.
for item in proofs:
 if not item['name'].endswith('/failed-task.json'):continue
 tasks=item['proof'].get('tasks',[])
 if len(tasks)!=1 or tasks[0].get('status',{}).get('state')!='FAILED':continue
 wave=item['name'].split('/')[-2]
 for event in tasks[0]['status'].get('statusEvents',[]):
  code=event.get('taskExecution',{}).get('exitCode')
  if code==50001:spot.append(wave)
  if code==50006 and 'VM is recreated during task execution' in event.get('description',''):recreated.append(wave)
# Prior generation-verified outcomes stay historical when trial storage expires.
history_file=P/'pre-lifecycle-outcomes.json'
previous=json.loads(history_file.read_text()) if history_file.exists() else {}
spot=sorted(set(spot)|set(previous.get('confirmed_spot_interruptions',[])))
deferred=sorted(set(deferred)|set(previous.get('deferred_admissions',[])))
recreated=sorted(set(recreated)|set(previous.get('confirmed_vm_recreations',[])))
other_failed.extend(json.loads(f.read_text())["wave"] for f in P.glob("storage-failed-case-*.json"))
other_failed=sorted(set(other_failed)|set(previous.get('other_failed_outcomes',[])))
collected=[json.loads(x.read_text()) for x in (R/'data/completed07').glob('wave-*/proof.json')]
assert all(x['passed'] for x in collected)
summary=dict(verified_complete=468+sum(len(x['cases']) for x in collected),target=2000,confirmed_spot_interruptions=spot,confirmed_vm_recreations=recreated,other_failed_outcomes=other_failed,deferred_admissions=deferred,earlier_excluded_admissions=[9,15],failed_zero_runtime_admissions=([514,515] if (P/'resume2-state.json').exists() else []),older_terminal_review=1)
save('pre-lifecycle-outcomes.json',summary);save('progress-summary.json',summary);print(json.dumps(summary))
