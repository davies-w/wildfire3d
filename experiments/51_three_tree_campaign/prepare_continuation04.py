"""Prepare unique04 never-started wave source; no cloud mutation or solver execution.
The interrupted case remains a separate checkpoint-only recovery, never a fresh deck run.
"""
from pathlib import Path
import json
R=Path(__file__).resolve().parent;P=R/'private04';P.mkdir(exist_ok=True)
assert not (P/'submission-intent.json').exists()
assert json.loads((R/'private03/closed.json').read_text())['passed']
s=(R/'package_campaign03.py').read_text().replace('campaign03','campaign04').replace("R/'private03'","R/'private04'").replace('data/cloud03','data/cloud04').replace('workflow03.yaml','workflow04.yaml').replace('wave03.yaml','wave04.yaml').replace('readiness03.yaml','readiness04.yaml').replace('launch-record03.json','launch-record04.json')
s=s.replace('if i<6:', 'if i<9:').replace('len(finished)==96 and len(set(finished))==96','len(finished)==150 and len(set(finished))==150').replace('1882','1828').replace('reused=117','reused=170').replace("{'completed_cases':117}","{'completed_cases':170}").replace('waves=105','waves=102').replace('!= 105','!= 102').replace("wave_id='wave-006'","wave_id='wave-009'")
s=s.replace("+json.loads((R/'private02/worker-proofs.json').read_text())", "+json.loads((R/'private02/worker-proofs.json').read_text())+json.loads((R/'private03/worker-proofs.json').read_text())")
s=s.replace("if x['name'].endswith('/completion.json')}\n", "if x['name'].endswith('/completion.json')}|{'tree51_000136_baseline'}\n")
s=s.replace('pending_terminal_review=1,','pending_terminal_review=1,pending_checkpoint_recovery=1,').replace("'pending_terminal_review':1,","'pending_terminal_review':1,'pending_checkpoint_recovery':1,")
(R/'package_campaign04.py').write_text(s)
s=(R/'cloud03.py').read_text().replace('campaign03','campaign04').replace("R/'private03'","R/'private04'");(R/'cloud04.py').write_text(s)
s=(R/'authorize_campaign03.py').read_text().replace('cloud03','cloud04').replace("R/'private02/", "R/'private03/");(R/'authorize_campaign04.py').write_text(s)
print('Prepared unique04 never-started package source; interruptedcase excluded pending checkpoint-only recovery')
