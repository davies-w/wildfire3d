"""Execute the actual worker preflight using native binary; no cloud submission."""
import json,subprocess
from pathlib import Path
from scene import ROOT
from sampling_test import BINARY
from overnight_grid_v2_control import cases
rows=[]
for c in cases():
 name=c['case'];job=ROOT/'jobs'/name;folder=ROOT/'data/grid_v2_worker_preflight'/name;folder.mkdir(parents=True,exist_ok=True);(folder/'decks').mkdir(exist_ok=True)
 (folder/'case.json').write_text((job/'case.json').read_text());(folder/'decks'/f'{name}.fds').write_text((ROOT/'decks'/f'{name}.fds').read_text())
 code=(job/'worker.py').read_text().split("folder=root/'data'/name")[0].replace('import runner',f'import types; runner=types.SimpleNamespace(BINARY={str(BINARY)!r})').replace("Path('/study')",f'Path({str(folder)!r})')
 with (folder/'test.log').open('w') as f:p=subprocess.run([str(ROOT.parents[1]/'.venv/bin/python'),'-c',code],stdout=f,stderr=subprocess.STDOUT,timeout=660)
 rows.append(dict(case=name,passed=p.returncode==0,scope='Actual worker preflight executed using native FDS; Linux worker repeats this gate before main solve.'))
 (ROOT/'results/overnight-grid-v2-worker-preflight.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,(folder/'test.log').read_text()
 print('PASS',name,flush=True)
