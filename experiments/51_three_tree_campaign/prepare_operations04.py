"""Generate unique04 operation tools without executing cloud actions."""
from pathlib import Path
R=Path(__file__).resolve().parent
assert not (R/'private04/submission-intent.json').exists()
for old,new in [('deploy_campaign03.py','deploy_campaign04.py'),('launch_campaign03.py','launch_campaign04.py'),('monitor_campaign03.py','monitor_campaign04.py'),('inspect_outputs03.py','inspect_outputs04.py')]:
 s=(R/old).read_text().replace('cloud03','cloud04').replace('campaign03','campaign04').replace('cloud03','cloud04').replace('workflow03.yaml','workflow04.yaml').replace('wave03.yaml','wave04.yaml').replace('readiness03.yaml','readiness04.yaml').replace('tree51-task-read03','tree51-task-read04')
 if old=='launch_campaign03.py':s=s.replace("R/'private02/closed.json'","R/'private03/closed.json'")
 if old=='deploy_campaign03.py':
  oldline="condition['expression']=condition['expression'].split(' && ')[0]+' && '+approved_expiry"
  newlines="controller_expression=condition['expression'].split(' && ')[0]+' && '+approved_expiry\ncondition['expression']='('+condition['expression'].split(' && ')[0]+\" || resource.name.startsWith('projects/_/buckets/tmrw-wildfire-20261015-trial/objects/tree51/campaign03/wave-008/tree51_000136_baseline/checkpoints/000/')\"+') && '+approved_expiry"
  assert oldline in s;s=s.replace(oldline,newlines)
  s=s.replace("title='tree51-campaign04-controller-read')","title='tree51-campaign04-controller-read',expression=controller_expression)")
 (R/new).write_text(s)
