"""Repackage only unsubmitted test jobs; scientific decks/splits unchanged."""
import json
from pathlib import Path
R=Path(__file__).parent;b=json.loads((R/'budget.json').read_text());assert all('test' not in n for n in b['reservations'])
p=R/'cloud.py';s=p.read_text();s=s.replace("count=2 if phase in ['pilot','domain'] else 3","count=1 if phase=='test' else 2 if phase in ['pilot','domain'] else 3")
s=s.replace("duration_s=5400,allowance_usd=.22)","duration_s=2400 if phase=='test' else 5400,allowance_usd=.10 if phase=='test' else .22)")
s=s.replace("ass[0]['deadline']='${sys.now() + 5280}'","ass[0]['deadline']='${sys.now() + '+str(g['duration_s']-120)+'}'")
s=s.replace("task['maxRunDuration']='5160s'","task['maxRunDuration']=str(g['duration_s']-240)+'s'")
p.write_text(s)
