"""Summarize independently collected successes and pinned interruption evidence."""
from cloud07 import *
proofs=json.loads((P/'worker-proofs.json').read_text())
outcomes=[x for x in proofs if x['name'].startswith(PREFIX+'outcomes/') and not x['proof']['passed']]
spot=[];deferred=[]
for x in outcomes:
 outcome=x['proof'];wave=outcome['wave']
 if outcome.get('spot'):
  tasks=[v for v in proofs if v['name']==PREFIX+wave+'/failed-task.json'];assert len(tasks)==1
  events=tasks[0]['proof']['tasks'][0]['status']['statusEvents'];assert any(e.get('taskExecution',{}).get('exitCode')==50001 for e in events)
  spot.append(wave)
 elif outcome.get('admission_deferred'):deferred.append(wave)
collected=[json.loads(x.read_text()) for x in (R/'data/completed07').glob('wave-*/proof.json')]
assert all(x['passed'] for x in collected)
summary=dict(verified_complete=468+sum(len(x['cases']) for x in collected),target=2000,confirmed_spot_interruptions=spot,deferred_admissions=deferred,earlier_excluded_admissions=[9,15],older_terminal_review=1)
save('progress-summary.json',summary);print(json.dumps(summary))
