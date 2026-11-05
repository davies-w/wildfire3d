"""Pin the failed creation step; never infer absence from a 502 response."""
from cloud05 import *
f=json.loads((P/'failure-5b1f159e-ce30-44ea-a981-a4c12ae89cd2.json').read_text());a=json.loads(f['argument']);assert a['index']==71 and f['state']=='FAILED'
err=json.loads(f['error']['payload']);assert err['code']==502
steps=json.loads((P/'failed71-failed-steps.json').read_text());assert not steps.get('nextPageToken');assert any(x['routine']=='main' and x['step']=='create' and x['state']=='STATE_FAILED' for x in steps['stepEntries'])
item=json.loads((R/'data/cloud05/inputs/items/71.json').read_text());objects=json.loads((P/'objects.json').read_text());case_objects=[x for x in objects if x['name'].startswith(PREFIX+item['id']+'/')]
save('creation-failure-review.json',dict(passed=True,classification='Batch_create_HTTP_502_ambiguous_submission',case=item['case'],index=71,execution=f['name'],creation_step_failed=True,post_retried=False,solver_failure_evidenced=False,case_objects_observed=[x['name'] for x in case_objects],absence_of_resources_not_yet_proven=True,requires_terminal_allocation_audit=True))
print('Creation502 pinned; resource/attempt eligibility remains pending terminal allocation audit')
