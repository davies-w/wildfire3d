"""One independent repeat to expose baseline run-to-run differences."""
from benchmark import ROOT,run,write_json
from transport import make_deck
name='transport_01_repeat'
d=run(name,make_deck(name,800,0.5,3,'reference'),timeout=600,
      scope='synthetic coupled reference repeat; one repeat cannot characterize variance')
write_json(ROOT/'results/reference_repeat.json',d)
if d['status']!='complete':raise SystemExit('Reference repeat failed')
