"""Freeze audited remaining cases in a unique namespace; no submission."""
from pathlib import Path
import json,hashlib,lzma,sys,time
R=Path(__file__).resolve().parent;P=R/'private07';D=R/'data/cloud07';assert not D.exists() and not (P/'submission-intent.json').exists();P.mkdir(exist_ok=True)
closed=json.loads((R/'private06/closed.json').read_text());assert closed['passed'] and closed['remainder_reserved_to']=='fds-tree51-campaign07'
assert json.loads((R/'private06/interrupted-case-review.json').read_text())['passed']
sys.path.insert(0,str(R/'rolling_fallback'));from prepare_rolling import render
D.mkdir();(D/'inputs/items').mkdir(parents=True)
selected=[]
for i,oldindex in enumerate([171,12,17]+list(range(176,1704))):
 old=R/'data/cloud06/inputs';item=json.loads((old/'items'/f'{oldindex}.json').read_text());blob=(old/(item['id']+'.xz')).read_bytes();assert hashlib.sha256(blob).hexdigest()==item['sha256'];payload=json.loads(lzma.decompress(blob));cases=json.loads(payload['groups.json'])['wave'];assert len(cases)==1 and cases[0]['pilot_case']==item['case'];c=cases[0];deck=payload['decks/'+item['case']+'.fds'];assert hashlib.sha256(deck.encode()).hexdigest()==c['deck_sha256'];assert 'recovery.json' not in payload
 for n in ['transport.py','checkpoint_control.py']:payload[n]=payload[n].replace('t51r06','t51r07')
 wave=f'wave-{i:06d}';blob=lzma.compress(json.dumps(payload).encode(),preset=1);(D/'inputs'/(wave+'.xz')).write_bytes(blob);(D/'inputs/items'/f'{i}.json').write_text(json.dumps(dict(index=i,id=wave,count=1,case=item['case'],sha256=hashlib.sha256(blob).hexdigest()),indent=2)+'\n');selected.append(item['case'])
assert len(set(selected))==1531 and selected[0]=='tree51_000446_baseline' and 'tree51_000088_baseline' not in selected
accepted={x['name'].split('/')[-2] for x in json.loads((R/'private06/worker-proofs.json').read_text()) if x['name'].endswith('/completion.json') and x['proof']['passed']};assert len(accepted)==173 and not accepted.intersection(selected)
for n,s in render('t51r07').items():(D/n).write_text(s);(R/('rolling07-'+n)).write_text(s)
index=dict(count=1531,reviewed=True,checkpoint_seconds=300,prior_completed=468,namespace='t51r07',first_case=selected[0],pending_terminal_review=1,fresh_count=1528,diagnosed_fresh_replacements=3);(D/'inputs/index.json').write_text(json.dumps(index,indent=2)+'\n')
b=json.loads((R.parent/'33_representation_loss/budget.json').read_text());hold=b['reservations']['fds-tree51-campaign07'];assert hold['state']=='reserved_before_upload' and hold['allowance_usd']==closed['remaining_allowance_usd'];assert b['reservations']['fds-tree51-training']['allowance_usd']==20 and b['estimated_spend_usd']+b['reserved_usd']<=b['authorized_usd']==200
old=json.loads((R/'private06/authorization.json').read_text());old.update(campaign_allowance_usd=hold['allowance_usd'],compute_limit_usd=hold['allowance_usd']-10,scope='Approved rolling continuation from terminally audited original remainder;1528never-submitted+3diagnosedlost-checkpointreplacements',recorded_unix=time.time())
for n,x in [('authorization.json',old),('reservation.json',dict(passed=True,allowance_usd=hold['allowance_usd'],compute_limit_usd=hold['allowance_usd']-10,training_reserved_usd=20)),('selection.json',selected),('permission-approval.json',json.loads((R/'private06/permission-approval.json').read_text()))]:(P/n).write_text(json.dumps(x,indent=2)+'\n')
files={str(f.relative_to(D)):hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file()};(P/'package.json').write_text(json.dumps(dict(cases=1531,fresh_cases=1528,diagnosed_fresh_replacements=3,prior_completed=468,pending_terminal_review=1,namespace='t51r07',files=files,index_sha256=files['inputs/index.json'],max_parallel_cpus=72,first_case=selected[0]),indent=2)+'\n');print('Prepared1531exactdecks;no submission',flush=True)
