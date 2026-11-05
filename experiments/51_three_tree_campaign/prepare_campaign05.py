"""Freeze the approved, audited rolling continuation; never deploy or submit."""
from pathlib import Path
import json,sys,time,hashlib,lzma,shutil
R=Path(__file__).resolve().parent;P=R/'private05';D=R/'data/cloud05'
assert not (P/'submission-intent.json').exists() and not D.exists()
closed=json.loads((R/'private04/closed.json').read_text());assert closed['passed'] and closed['remainder_reserved_to']=='fds-tree51-campaign05'
approval=json.loads((R/'private04/continuation-authorization.json').read_text());assert approval['rolling_fallback_authorized']
P.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'rolling_fallback'));from prepare_rolling import prepare
manifest=json.loads((R/'data/cloud04/manifest.json').read_text());fresh=[];replacement=None
for item in manifest:
 payload=json.loads(lzma.decompress((R/'data/cloud04'/(item['id']+'.xz')).read_bytes()));group=json.loads(payload['groups.json'])['wave']
 if int(item['id'][5:])>=12:fresh.extend(c['pilot_case'] for c in group)
 if item['id']=='wave-011':replacement=group[2]['pilot_case']
assert replacement=='tree51_000187_baseline' and len(fresh)==1774
lost=json.loads((R/'private04/interrupted-case-review.json').read_text());assert lost['failure']=='confirmed_Spot_preemption_50001' and lost['startup_passed'] and not lost['restart_checkpoint_available'] and not lost['final_archive_available']
# One explicitly diagnosed replacement attempt, not a claim of checkpoint recovery.
selected=[replacement]+fresh;assert len(set(selected))==1775 and 'tree51_000088_baseline' not in selected
prior=set()
for folder in ['private','private02','private03','private04']:
 for x in json.loads((R/folder/'worker-proofs.json').read_text()):
  if x['name'].endswith('/completion.json') and x['proof']['passed']:prior.add(x['name'].split('/')[-2])
assert len(prior)==202 and not prior.intersection(selected)  # plus22 original reused
prepare(R/'data/cloud04',selected,'t51r05',D)
for name in ['parent.yaml','epoch.yaml','case.yaml']:
 assert (D/name).read_text()==(R/('rolling05-'+name)).read_text()
index=json.loads((D/'inputs/index.json').read_text());index.update(reviewed=True,checkpoint_seconds=480,prior_completed=224,first_case=replacement,pending_terminal_review=1,fresh_count=1774,diagnosed_replacement_count=1)
(D/'inputs/index.json').write_text(json.dumps(index,indent=2)+'\n')
(P/'selection.json').write_text(json.dumps(selected,indent=2)+'\n')
(P/'replacement-review.json').write_text(json.dumps(dict(case=replacement,reason='confirmed50001; passing startup; terminal archive inventory proves no saved state',mode='single_diagnosed_fresh_replacement_from_zero',prior_work_lost=True,no_automatic_retry=True,authorization=approval),indent=2)+'\n')
b=json.loads((R.parent/'33_representation_loss/budget.json').read_text());hold=b['reservations']['fds-tree51-campaign05'];assert hold['state']=='reserved_before_upload';allowance=hold['allowance_usd'];assert allowance==closed['remaining_allowance_usd'];assert b['reservations']['fds-tree51-training']['allowance_usd']==20 and b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
old=json.loads((R/'private04/authorization.json').read_text());auth=dict(old,campaign_allowance_usd=allowance,compute_limit_usd=allowance-10,scope='Explicit rolling continuation approval;1774neverstarted+1diagnosedSpotreplacement;originalallowanceonly',recorded_unix=time.time());(P/'authorization.json').write_text(json.dumps(auth,indent=2)+'\n');(P/'reservation.json').write_text(json.dumps(dict(passed=True,allowance_usd=allowance,compute_limit_usd=allowance-10,training_reserved_usd=20),indent=2)+'\n')
(P/'permission-approval.json').write_text(json.dumps(dict(original=json.loads((R/'private02/permission-approval.json').read_text()),continuation=approval),indent=2)+'\n')
files={str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(D.rglob('*')) if f.is_file()}
package=dict(cases=1775,fresh_cases=1774,diagnosed_replacement_cases=1,prior_completed=224,pending_terminal_review=1,namespace='t51r05',files=files,index_sha256=files['inputs/index.json'],max_parallel_cpus=72,first_case=replacement)
(P/'package.json').write_text(json.dumps(package,indent=2)+'\n')
print('Prepared1775singletons;224completedexcluded;oldterminalreviewexcluded;no cloud submission')
