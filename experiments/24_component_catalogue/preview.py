from pathlib import Path
import json
r=Path(__file__).parent
text=(r/'catalogue.template.html').read_text().replace('CATALOGUE_DATA',json.dumps(json.loads((r/'data/catalogue.json').read_text()),separators=(',',':')))
(r/'data/catalogue.html').write_text(text)
