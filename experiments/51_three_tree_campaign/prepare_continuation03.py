"""Prepare unique campaign03 from frozen inputs; never submit or modify campaign02."""
from pathlib import Path
R=Path(__file__).resolve().parent;P=R/'private03';P.mkdir(exist_ok=True)
assert not (P/'submission-intent.json').exists()
s=(R/'package_campaign02.py').read_text().replace('campaign02','campaign03').replace("R/'private02'","R/'private03'").replace('data/cloud02','data/cloud03').replace('workflow02.yaml','workflow03.yaml').replace('wave02.yaml','wave03.yaml').replace('readiness02.yaml','readiness03.yaml').replace('launch-record02.json','launch-record03.json')
s=s.replace('if i<5:', 'if i<6:').replace('len(finished)==78 and len(set(finished))==78','len(finished)==96 and len(set(finished))==96').replace('==1900','==1882').replace('new_cases=1900,reused=100,waves=106','new_cases=1882,reused=117,pending_terminal_review=1,waves=105').replace("{'completed_cases':100}","{'completed_cases':117}").replace('!= 106','!= 105').replace("wave_id='wave-005'","wave_id='wave-006'")
s=s.replace("for n in ['worker.py','transport.py','checkpoint_control.py']:","payload['worker.py']=(R/'worker03.py').read_text()\n  payload['completion_check03.py']=(R/'completion_check03.py').read_text()\n  for n in ['worker.py','transport.py','checkpoint_control.py']:")
s=s.replace("proofs=json.loads((R/'private/worker-proofs.json').read_text())", "proofs=json.loads((R/'private/worker-proofs.json').read_text())+json.loads((R/'private02/worker-proofs.json').read_text())\n assert set(finished)=={x['name'].split('/')[-2] for x in proofs if x['name'].endswith('/completion.json')}\n assert sum(not x['proof']['passed'] for x in proofs if x['name'].endswith('/completion.json'))==1\n assert __import__('json').loads((R/'private02/terminal-scientific-review.json').read_text())['evidence_verified']")
s=s.replace("{'passed':True,'completed_case_count':'${completed_cases}'", "{'passed':True,'target_complete':False,'pending_terminal_review':1,'completed_case_count':'${completed_cases}'")
s=s.replace('lzma.compress(json.dumps(payload).encode())','lzma.compress(json.dumps(payload).encode(),preset=1)')
(R/'package_campaign03.py').write_text(s)
s=(R/'prepare_operations02.py').read_text().replace('02','03');(R/'prepare_operations03.py').write_text(s)
s=(R/'authorize_campaign02.py').read_text().replace('cloud02','cloud03').replace("R/'private/closed.json'","R/'private02/closed.json'").replace("R/'private/authorization.json'","R/'private02/authorization.json'");(R/'authorize_campaign03.py').write_text(s)
