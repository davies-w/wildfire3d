"""Summarize local gradient diagnostics, without treating them as training evidence."""
import json, math, statistics
from pathlib import Path
R=Path(__file__).resolve().parent

def summarize(report):
 rows=report['rows']
 assert len(rows)==54, f'Expected 54 diagnostic windows, got {len(rows)}'
 out={'interpretation':'Within-architecture local gradients only; no optimizer steps. Negative cosines do not establish causal training failure. Candidate radiation loss uses three-frame windows, not full-history dose.', 'groups':{}}
 for arm in sorted({r['arm'] for r in rows}):
  selected=[r for r in rows if r['arm']==arm]
  assert len({r['case'] for r in selected})==6
  assert len({tuple(r['parameter_scope']) for r in selected})==1
  for phase in [None,10,30,120]:
   rr=selected if phase is None else [r for r in selected if abs(r['time_s'][0]-phase)<2]
   assert len(rr)==(18 if phase is None else 6)
   norms={}
   for name in rr[0]['gradient_norms']:
    values=[r['gradient_norms'][name] for r in rr]
    assert all(math.isfinite(v) and v>=0 for v in values)
    norms[name]={'median':statistics.median(values),'min':min(values),'max':max(values),'zero_count':sum(v==0 for v in values)}
   cos={}
   for name in rr[0]['gradient_cosines']:
    values=[r['gradient_cosines'][name] for r in rr if r['gradient_cosines'][name] is not None]
    assert all(math.isfinite(v) and abs(v)<=1.00001 for v in values)
    cos[name]={'median':statistics.median(values) if values else None,'negative_count':sum(v<0 for v in values),'defined_count':len(values)}
   out['groups'][arm+'/'+('all_windows' if phase is None else str(phase)+'s')]={'windows':len(rr),'checkpoint_step':rr[0]['checkpoint_step'],'parameter_scope':rr[0]['parameter_scope'],'norms':norms,'cosines':cos}
 return out

if __name__=='__main__':
 report=json.loads((R/'data/collected/report.json').read_text())
 (R/'results/gradient-summary.json').write_text(json.dumps(summarize(report),indent=2)+'\n')
