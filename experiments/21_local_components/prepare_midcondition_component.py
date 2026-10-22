"""Targeted training addition after local validation exposed condition interpolation error.
Validation is used for development; Stage C geometry/outcomes remain untouched.
"""
import json,os,subprocess
from scene import ROOT
from component_campaign import build
from sampling_test import BINARY
name='b21_single_midcondition';ledger=json.loads((ROOT/'budget-overnight.json').read_text());assert name not in ledger['reservations'];c=dict(case=name,split='train',family='single',gap_m=4,wind_m_s=3,direction=270,moisture=.11,receiver_large=False)
s,r=build(c);r['sampling_note']='Added after local validation: wind/moisture match single_validation, but facade gap4m versus2m. This is adaptive development, not untouched validation. Stage C unchanged.'
p=ROOT/'component-development.json';d=json.loads(p.read_text());d['cases']=[x for x in d['cases'] if x['case']!=name]+[r];p.write_text(json.dumps(d,indent=2));(ROOT/'decks'/f'{name}.fds').write_text(s)
w=ROOT/'data/component_preflight'/name;w.mkdir(exist_ok=True);(w/'check.fds').write_text(s.replace('T_END=90','T_END=.6').replace('DT_RESTART=10.','DT_RESTART=100000.'))
with (w/'run.log').open('w') as f:proc=subprocess.run([str(BINARY),'check.fds'],cwd=w,env=dict(os.environ,OMP_NUM_THREADS='4',OMP_WAIT_POLICY='PASSIVE',GOMP_SPINCOUNT='0'),stdout=f,stderr=subprocess.STDOUT,timeout=300)
assert proc.returncode==0 and 'completed successfully' in (w/'run.log').read_text().lower();(ROOT/'results/midcondition-preflight.json').write_text(json.dumps(dict(case=name,passed=True,deck_sha256=r['deck_sha256'],allowance_usd=.25),indent=2));print('Passed',name,'not submitted')
