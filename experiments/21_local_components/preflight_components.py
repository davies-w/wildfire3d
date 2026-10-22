import json,os,subprocess
from scene import ROOT
from sampling_test import BINARY
rows=[]
for name in ['b21_single_0','b21_transfer_1','b21_combined_1','b21_corner_1']:
 w=ROOT/'data/component_preflight'/name;w.mkdir(parents=True,exist_ok=True);s=(ROOT/'decks'/f'{name}.fds').read_text().replace('T_END=90','T_END=.6').replace('DT_RESTART=10.','DT_RESTART=100000.');(w/'check.fds').write_text(s)
 with (w/'run.log').open('w') as f:p=subprocess.run([str(BINARY),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=300)
 ok=p.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower();rows.append(dict(case=name,passed=ok));(ROOT/'results/component-preflight.json').write_text(json.dumps(rows,indent=2));assert ok,(w/'run.log').read_text()[-2000:];print('PASS',name,flush=True)
