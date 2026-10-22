import json
from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'data/catalogue.json';d=json.loads(p.read_text())
(R/'data/catalogue.html').write_text((R/'catalogue.template.html').read_text().replace('PAYLOAD',json.dumps(d,separators=(',',':'))))
assert (R/'data/catalogue.html').stat().st_size<1000000
print('Preview bytes',(R/'data/catalogue.html').stat().st_size)
