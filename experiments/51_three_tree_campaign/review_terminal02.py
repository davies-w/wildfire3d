"""Separate scientific end-time evidence from the unchanged failed operational status."""
from cloud02 import *
from completion_check03 import terminal_success
import csv,math
root=P/'failure-inspection/evidence';result=json.loads((root/'result.json').read_text());case=json.loads((root/'input.json').read_text())['case'];name=case['pilot_case'];checkpoint=json.loads((root/'solve/checkpoint.json').read_text());assert checkpoint['physical_time']==180 and checkpoint['step']==1920
rows_by_kind={}
for kind in ['devc','hrr']:
 path=root/'solve'/(name+'_'+kind+'.csv')
 with path.open() as f:
  rows=csv.reader(f);next(rows);headers=[x.strip().strip('"') for x in next(rows)];data=[[float(x) for x in row] for row in rows if row]
 ti=headers.index('Time');times=[r[ti] for r in data];assert times[-1]>=180-1e-6 and all(b>=a for a,b in zip(times,times[1:])) and all(math.isfinite(x) for row in data for x in row)
 rows_by_kind[kind]=dict(rows=len(data),first_time=times[0],last_time=times[-1],sha256=sha(path))
startup=json.loads((root/'startup.json').read_text());assert startup['passed'] and startup['mass_check_time_s']<=.100001 and max(startup['mass_relative_error'].values())<.01
first=result['segments'][0];assert terminal_success(first,rows_by_kind['devc']['last_time'],root/'solve'/first['log'])
second=result['segments'][1];assert not terminal_success(second,180,root/'solve'/second['log'])
save('terminal-scientific-review.json',dict(evidence_verified=True,case=name,clean_terminal_time_s=180,checkpoint_step=1920,records=rows_by_kind,first_segment_log_sha256=sha(root/'solve'/first['log']),original_batch_status='FAILED',original_completion_passed=False,operationally_accepted=False,disposition='Preserve without rerun; terminal scientific salvage requires explicitly qualified acceptance; never rewrite original status'))
print('Terminal180s/device/HRR/initialmass evidence verified; original operational failure unchanged')
