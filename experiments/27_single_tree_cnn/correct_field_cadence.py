"""Correct only unsubmitted inputs; preserve pilot bytes and original freeze."""
import json,hashlib
from pathlib import Path
R=Path(__file__).parent
ledger=json.loads((R/'budget.json').read_text());reserved={c for g in ledger['reservations'].values() for c in g['cases']}
assert all(n.startswith('s27_pilot_') for n in reserved)
original=R/'results/initial-input-freeze.json';assert not original.exists();original.write_bytes((R/'results/input-freeze.json').read_bytes())
p=R/'build.py';s=p.read_text();s=s.replace(" if c.get('expanded'):"," if c['split']!='pilot':s=s.replace('DT_SLCF=2.,','DT_SLCF=2., DT_SL3D=2.,')\n if c.get('expanded'):");p.write_text(s)
from build import deck
rows=json.loads((R/'cases.json').read_text());ts=json.loads((R/'data/tree-templates.json').read_text());changed=[]
for c in rows:
 path=R/'decks'/(c['case']+'.fds')
 if c['case'] in reserved:assert hashlib.sha256(path.read_bytes()).hexdigest()==c['deck_sha256'];continue
 source,_=deck(c,ts);path.write_text(source);c['deck_sha256']=hashlib.sha256(source.encode()).hexdigest();changed.append(c['case'])
(R/'cases.json').write_text(json.dumps(rows,indent=2)+'\n');freeze=json.loads(original.read_text());freeze['cases']={c['case']:c['deck_sha256'] for c in rows};freeze['cadence_correction']='Unsubmitted nonpilot cases explicitly DT_SL3D=2. Pilot bytes unchanged; volume frames every36s.';(R/'results/input-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
p=R/'cloud.py';s=p.read_text().replace(" verify();assert not (ROOT/'budget.json').exists()"," verify();reserved=read('budget.json')['reservations'] if (ROOT/'budget.json').exists() else {}")
s=s.replace("   runner=(ROOT/'runner-template.py')","   if name in reserved:\n    assert read(f'jobs/{name}/group.json')==g;groups.append(g);continue\n   runner=(ROOT/'runner-template.py')")
p.write_text(s)
(R/'results/cadence-correction.json').write_text(json.dumps(dict(changed_unsubmitted=changed,preserved_submitted=sorted(reserved),cause='FDS DT_SL3D defaults to horizon/5; DT_SLCF does not govern volume fields'),indent=2))
